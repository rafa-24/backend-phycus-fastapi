from collections import defaultdict
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlmodel import Session, select

from app.modules.analytics.schema.analytics_schema import (
    AnalyticsDashboardResponse,
    DailyRevenuePoint,
    MetricCard,
    MonthlyGrowthPoint,
    ProductSalesRank,
    StockAlertItem,
    StockProjectionItem,
)
from app.modules.orders.models.order_model import OrderItems, Orders
from app.modules.products.models.product_model import Products
from app.modules.shared.exceptions.app_exceptions import NotFoundException
from app.modules.shared.schemas.api_response import ApiResponse
from app.modules.stores.repository.store_repository import StoreRepository

DEFAULT_SAFETY_STOCK = 10
DAY_LABELS_ES = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
MONTH_LABELS_ES = [
    "Ene",
    "Feb",
    "Mar",
    "Abr",
    "May",
    "Jun",
    "Jul",
    "Ago",
    "Sep",
    "Oct",
    "Nov",
    "Dic",
]


class AnalyticsService:
    def __init__(self):
        self.store_repository = StoreRepository()

    def _get_store_or_raise(self, session: Session, store_id: int):
        store = self.store_repository.get_by_id(session, store_id)
        if not store:
            raise NotFoundException("No existe una tienda con ese identificador.")
        return store

    def _format_money(self, value: float) -> str:
        amount = int(round(value))
        return f"$ {amount:,}".replace(",", ".")

    def _pct_change(self, current: float, previous: float) -> float | None:
        if previous <= 0:
            return 100.0 if current > 0 else 0.0
        return round(((current - previous) / previous) * 100, 1)

    def _approved_orders(
        self,
        session: Session,
        store_id: int,
        start: datetime,
        end: datetime,
    ) -> list[Orders]:
        statement = (
            select(Orders)
            .where(Orders.store_id == store_id)
            .where(Orders.payment_status == "approved")
            .where(Orders.created_at >= start)
            .where(Orders.created_at < end)
        )
        return list(session.exec(statement).all())

    def _order_items_for_orders(
        self, session: Session, order_ids: list[int]
    ) -> list[OrderItems]:
        if not order_ids:
            return []
        statement = select(OrderItems).where(OrderItems.order_id.in_(order_ids))
        return list(session.exec(statement).all())

    def get_dashboard(self, session: Session, store_id: int):
        store = self._get_store_or_raise(session, store_id)
        now = datetime.now(UTC)
        # Normaliza a naive UTC si la BD guarda naive
        if now.tzinfo is not None:
            now_naive = now.replace(tzinfo=None)
        else:
            now_naive = now

        today_start = datetime(
            now_naive.year, now_naive.month, now_naive.day
        )
        week_start = today_start - timedelta(days=6)
        week_end = today_start + timedelta(days=1)
        prev_week_start = week_start - timedelta(days=7)
        prev_week_end = week_start

        current_orders = self._approved_orders(
            session, store_id, week_start, week_end
        )
        previous_orders = self._approved_orders(
            session, store_id, prev_week_start, prev_week_end
        )

        current_revenue = float(
            sum(Decimal(str(o.total or 0)) for o in current_orders)
        )
        previous_revenue = float(
            sum(Decimal(str(o.total or 0)) for o in previous_orders)
        )
        current_count = len(current_orders)
        previous_count = len(previous_orders)
        avg_ticket = (
            current_revenue / current_count if current_count > 0 else 0.0
        )
        prev_avg = (
            previous_revenue / previous_count if previous_count > 0 else 0.0
        )

        products = list(
            session.exec(
                select(Products).where(Products.store_id == store_id)
            ).all()
        )
        active_products = [p for p in products if p.is_active]
        safety = DEFAULT_SAFETY_STOCK
        alerts = [
            p
            for p in active_products
            if p.stock is not None and int(p.stock) <= safety
        ]

        # Ingresos diarios (últimos 7 días)
        daily_map: dict[str, float] = defaultdict(float)
        for order in current_orders:
            created = order.created_at
            if created.tzinfo is not None:
                created = created.replace(tzinfo=None)
            key = created.strftime("%Y-%m-%d")
            daily_map[key] += float(Decimal(str(order.total or 0)))

        daily_revenue: list[DailyRevenuePoint] = []
        for offset in range(7):
            day = week_start + timedelta(days=offset)
            key = day.strftime("%Y-%m-%d")
            daily_revenue.append(
                DailyRevenuePoint(
                    date=key,
                    label=DAY_LABELS_ES[day.weekday()],
                    revenue=round(daily_map.get(key, 0.0), 2),
                )
            )

        # Crecimiento mensual (últimos 6 meses)
        month_cursor = datetime(now_naive.year, now_naive.month, 1)
        months: list[tuple[datetime, datetime]] = []
        for _ in range(6):
            if month_cursor.month == 12:
                next_month = datetime(month_cursor.year + 1, 1, 1)
            else:
                next_month = datetime(
                    month_cursor.year, month_cursor.month + 1, 1
                )
            months.append((month_cursor, next_month))
            month_cursor = (
                datetime(month_cursor.year, month_cursor.month - 1, 1)
                if month_cursor.month > 1
                else datetime(month_cursor.year - 1, 12, 1)
            )
        months.reverse()

        monthly_growth: list[MonthlyGrowthPoint] = []
        prev_month_rev: float | None = None
        for start, end in months:
            month_orders = self._approved_orders(session, store_id, start, end)
            rev = float(sum(Decimal(str(o.total or 0)) for o in month_orders))
            growth = (
                None
                if prev_month_rev is None
                else self._pct_change(rev, prev_month_rev)
            )
            monthly_growth.append(
                MonthlyGrowthPoint(
                    month=start.strftime("%Y-%m"),
                    label=MONTH_LABELS_ES[start.month - 1],
                    revenue=round(rev, 2),
                    growth_percent=growth,
                )
            )
            prev_month_rev = rev

        # Ranking por unidades (semana actual)
        order_ids = [o.id for o in current_orders if o.id is not None]
        items = self._order_items_for_orders(session, order_ids)
        sales_by_product: dict[str, dict] = {}
        for item in items:
            key = (
                f"id:{item.product_id}"
                if item.product_id is not None
                else f"name:{item.product_name}"
            )
            bucket = sales_by_product.setdefault(
                key,
                {
                    "product_id": item.product_id,
                    "product_name": item.product_name,
                    "product_image_url": item.product_image_url,
                    "units_sold": 0,
                    "revenue": 0.0,
                },
            )
            bucket["units_sold"] += int(item.quantity or 0)
            bucket["revenue"] += float(Decimal(str(item.line_total or 0)))

        ranked = sorted(
            sales_by_product.values(),
            key=lambda row: row["units_sold"],
            reverse=True,
        )
        top_products = [
            ProductSalesRank(
                product_id=row["product_id"],
                product_name=row["product_name"],
                product_image_url=row["product_image_url"],
                units_sold=row["units_sold"],
                revenue=round(row["revenue"], 2),
            )
            for row in ranked[:5]
        ]

        # Movimiento lento: activos con menos ventas (incluye 0)
        units_by_id = {
            row["product_id"]: row["units_sold"]
            for row in ranked
            if row["product_id"] is not None
        }
        slow_candidates = []
        for product in active_products:
            units = units_by_id.get(product.id, 0)
            slow_candidates.append(
                ProductSalesRank(
                    product_id=product.id,
                    product_name=product.name,
                    product_image_url=product.image_url,
                    units_sold=units,
                    revenue=0.0,
                )
            )
        slow_products = sorted(
            slow_candidates, key=lambda row: row.units_sold
        )[:5]

        # Proyección de compras: top vendidos con stock
        projection: list[StockProjectionItem] = []
        for row in ranked[:6]:
            product = next(
                (p for p in products if p.id == row["product_id"]), None
            )
            if not product:
                continue
            stock = int(product.stock or 0)
            demand = int(row["units_sold"])
            projection.append(
                StockProjectionItem(
                    product_id=product.id,
                    product_name=product.name,
                    product_image_url=product.image_url,
                    current_stock=stock,
                    projected_demand=max(demand, 1),
                )
            )

        stock_alerts = [
            StockAlertItem(
                product_id=product.id,
                product_name=product.name,
                product_image_url=product.image_url,
                sku_label=f"ID-{product.id}",
                current_stock=int(product.stock or 0),
                safety_stock=safety,
                restock_qty=max(safety * 2 - int(product.stock or 0), safety),
            )
            for product in sorted(
                alerts, key=lambda p: int(p.stock or 0)
            )[:8]
        ]

        dashboard = AnalyticsDashboardResponse(
            store_name=store.name,
            week_revenue=MetricCard(
                label="Ingresos semana",
                value=round(current_revenue, 2),
                display_value=self._format_money(current_revenue),
                change_percent=self._pct_change(
                    current_revenue, previous_revenue
                ),
            ),
            week_orders=MetricCard(
                label="Pedidos",
                value=float(current_count),
                display_value=str(current_count),
                change_percent=self._pct_change(
                    float(current_count), float(previous_count)
                ),
            ),
            average_ticket=MetricCard(
                label="Ticket promedio",
                value=round(avg_ticket, 2),
                display_value=self._format_money(avg_ticket),
                change_percent=self._pct_change(avg_ticket, prev_avg),
            ),
            active_skus=MetricCard(
                label="SKUs activos",
                value=float(len(active_products)),
                display_value=str(len(active_products)),
                alert_count=len(alerts),
            ),
            daily_revenue=daily_revenue,
            monthly_growth=monthly_growth,
            top_products=top_products,
            slow_products=slow_products,
            purchase_projection=projection,
            stock_alerts=stock_alerts,
            generated_at=datetime.now(UTC),
        )

        return ApiResponse(
            message="Analítica generada correctamente.",
            data=dashboard,
        )
