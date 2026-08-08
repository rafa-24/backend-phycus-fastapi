from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel


class MetricCard(SQLModel):
    label: str
    value: float
    display_value: str
    change_percent: Optional[float] = None
    alert_count: Optional[int] = None


class DailyRevenuePoint(SQLModel):
    date: str
    label: str
    revenue: float


class MonthlyGrowthPoint(SQLModel):
    month: str
    label: str
    revenue: float
    growth_percent: Optional[float] = None


class ProductSalesRank(SQLModel):
    product_id: Optional[int] = None
    product_name: str
    product_image_url: Optional[str] = None
    units_sold: int
    revenue: float


class StockProjectionItem(SQLModel):
    product_id: int
    product_name: str
    product_image_url: Optional[str] = None
    current_stock: int
    projected_demand: int


class StockAlertItem(SQLModel):
    product_id: int
    product_name: str
    product_image_url: Optional[str] = None
    sku_label: str
    current_stock: int
    safety_stock: int
    restock_qty: int


class AnalyticsDashboardResponse(SQLModel):
    store_name: str
    week_revenue: MetricCard
    week_orders: MetricCard
    average_ticket: MetricCard
    active_skus: MetricCard
    daily_revenue: list[DailyRevenuePoint]
    monthly_growth: list[MonthlyGrowthPoint]
    top_products: list[ProductSalesRank]
    slow_products: list[ProductSalesRank]
    purchase_projection: list[StockProjectionItem]
    stock_alerts: list[StockAlertItem]
    generated_at: datetime
