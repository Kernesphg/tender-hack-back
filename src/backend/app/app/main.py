from statistics import mean
from typing import Dict

import numpy as np
from sqlalchemy import Column, ForeignKey, Integer, String, Boolean, Float, DateTime, create_engine

from sqlalchemy.orm import declarative_base, relationship
from collections import defaultdict
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from sqlalchemy import distinct
from collections import Counter


from fastapi.middleware.cors import CORSMiddleware

engine = create_engine('postgresql://ezz:ezz@92.51.38.68:5432/ezz', echo=True)  # sqlite:///hack_data.db
Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()


class KsData(Base):
    __tablename__ = 'ks_data'
    index = Column(Integer, primary_key=True)
    participant_inn = Column(Integer)
    is_winner = Column(Boolean)
    ks_id = Column(Integer)
    publish_date = Column(DateTime)
    price = Column(Float)
    customer_inn = Column(Integer)
    customer_type = Column(String)
    kpgz = Column(String)
    region_code = Column(Integer)
    violations = Column(Boolean)


class ContractsData(Base):
    __tablename__ = 'contracts_data'
    index = Column(Integer, primary_key=True)
    ks_id = Column(Integer)
    contract_id = Column(Integer)
    conclusion_date = Column(DateTime)
    price = Column(Float)
    customer_inn = Column(Integer)
    supplier_inn = Column(Integer)
    violations = Column(Boolean)
    status = Column(Boolean)


class BlockingData(Base):
    __tablename__ = 'blocking_data'
    index = Column(Integer, primary_key=True)
    supplier_inn = Column(Integer)
    reason = Column(String)
    blocking_start_date = Column(DateTime)
    blocking_end_date = Column(DateTime)


class Contract_executionData(Base):
    __tablename__ = 'contract_execution_data'
    index = Column(Integer, primary_key=True)
    contract_id = Column(Integer)
    upd_id = Column(Integer)
    scheduled_delivery_date = Column(DateTime)
    actual_delivery_date = Column(DateTime)
    supplier_inn = Column(Integer)
    customer_inn = Column(Integer)


Base.metadata.create_all(engine)

###

from fastapi import FastAPI, APIRouter

app = FastAPI(
    title="tenderhack noname", openapi_url=f"/openapi.json"  # settings.PROJECT_NAME # settings.API_V1_STR
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import pandas as pd

from sqlalchemy.sql import func


def win_sum(supplier_inn: int, date_start: datetime = None, date_stop: datetime = None,
            kpgz: str = None, regions: list = None, price_range: list = None) -> float:
    # Выполнение запроса к базе данных через SQLAlchemy
    query = session.query(func.sum(KsData.price)).filter(
        KsData.participant_inn == supplier_inn,
        KsData.is_winner == 1  # Предполагается, что is_winner представлен в БД как булев тип
    )
    if kpgz:
        query = query.filter(KsData.kpgz == kpgz)
    if regions:
        query = query.filter(KsData.region_code.in_(regions))
    if price_range:
        query = query.filter(KsData.price.between(price_range[0], price_range[1]))
    if date_start and date_stop:
        query = query.filter(KsData.publish_date.between(date_start, date_stop))

    result = query.scalar() or 0.0  # В случае отсутствия данных вернуть 0.0
    return float(result)


def win_sum_by_date(supplier_inn: int, date_start: datetime = None, date_stop: datetime = None,
                    kpgz: str = None, regions: list = None,
                    price_range: list = None) -> dict:
    ks_query = session.query(KsData)
    contract_query = session.query(ContractsData)
    ks_query = ks_query.filter(KsData.participant_inn == supplier_inn, KsData.is_winner == 1)


    if not date_start or not date_stop:
        supplier_contracts = contract_query.filter(ContractsData.supplier_inn == supplier_inn).all()
        if not supplier_contracts:
            return {}

        min_date_str = min(contract.conclusion_date for contract in supplier_contracts)
        max_date_str = max(contract.conclusion_date for contract in supplier_contracts)

        # Преобразование строк в объекты datetime
        min_date = datetime.strptime(min_date_str, '%Y-%m-%d')
        max_date = datetime.strptime(max_date_str, '%Y-%m-%d')

        date_start = min_date if not date_start else date_start
        date_stop = max_date if not date_stop else date_stop

    ks_query = ks_query.filter(
        KsData.publish_date >= date_start.strftime('%Y-%m-%d'),
        KsData.publish_date <= date_stop.strftime('%Y-%m-%d')
    )

    if kpgz:
        ks_query = ks_query.filter(KsData.kpgz == kpgz)
    if regions:
        ks_query = ks_query.filter(KsData.region_code.in_(regions))
    if price_range:
        ks_query = ks_query.filter(KsData.price.between(price_range[0], price_range[1]))

    supplier_contracts = contract_query.filter(ContractsData.supplier_inn == supplier_inn).all()
    if not supplier_contracts:
        return {}

    completed_contracts = [contract.ks_id for contract in supplier_contracts if contract.status == 1]
    ks_query = ks_query.filter(KsData.ks_id.in_(completed_contracts))

    filtered_data = ks_query.all()
    grouped_data = pd.DataFrame([(data.publish_date, data.price) for data in filtered_data],
                                columns=["publish_date", "price"]).groupby("publish_date")["price"].sum().reset_index()
    return grouped_data.to_dict()


def get_user_activity(supplier_inn: int, date_start: datetime = None, date_stop: datetime = None,
                    kpgz: str = None, regions: list = None,
                    price_range: list = None):
    # Формирование фильтров на основе входных параметров
    filters = []

    if date_start:
        filters.append(ContractsData.conclusion_date >= date_start)
    if date_stop:
        filters.append(ContractsData.conclusion_date <= date_stop)
    if kpgz:
        filters.append(KsData.kpgz == kpgz)
    if regions:
        filters.append(KsData.region_code.in_(regions))
    if price_range:
        filters.append(ContractsData.price >= price_range[0])
        filters.append(ContractsData.price <= price_range[1])

    # Фильтрация данных из таблиц для пользователя с указанным inn
    user_data = session.query(ContractsData).join(KsData, ContractsData.ks_id == KsData.ks_id).filter(
        ContractsData.supplier_inn == supplier_inn, *filters).all()

    # Собираем данные по статусу контрактов для пользователя
    user_activity = defaultdict(list)
    for data in user_data:
        user_activity[data.conclusion_date].append(data.status)

    # Преобразование данных для отрисовки линейчатого графика
    timeline = []
    statuses = {'active': 0, 'inactive': 0, 'other': 0}
    for date, status_list in user_activity.items():
        active_count = status_list.count(True)
        inactive_count = status_list.count(False)
        other_count = len(status_list) - active_count - inactive_count

        statuses['active'] += active_count
        statuses['inactive'] += inactive_count
        statuses['other'] += other_count

        timeline.append({'date': date, 'active': active_count, 'inactive': inactive_count, 'other': other_count})

    return timeline, statuses


def get_user_regions(supplier_inn: int, date_start: datetime = None, date_stop: datetime = None,
                    kpgz: str = None, regions: list = None,
                    price_range: list = None):
    # Формирование фильтров на основе входных параметров
    filters = []

    if date_start:
        filters.append(KsData.publish_date >= date_start)
    if date_stop:
        filters.append(KsData.publish_date <= date_stop)
    if kpgz:
        filters.append(KsData.kpgz == kpgz)
    if regions:
        filters.append(KsData.region_code.in_(regions))
    if price_range:
        filters.append(KsData.price >= price_range[0])
        filters.append(KsData.price <= price_range[1])

    # Фильтрация данных из таблицы KsData для пользователя с указанным inn
    user_regions = session.query(distinct(KsData.region_code)).filter(
        KsData.participant_inn == supplier_inn, *filters).all()

    # Преобразование результатов запроса в список уникальных кодов регионов
    unique_regions = [region[0] for region in user_regions]

    return unique_regions


def top_kpgz_for_supplier(supplier_inn: int, date_start: datetime = None, date_stop: datetime = None,
                    kpgz: str = None, regions: list = None,
                    price_range: list = None):
    if kpgz:
        return []  # Если КПГЗ указаны в запросе, эта функция не возвращает ничего

    # Формирование фильтров на основе входных параметров
    filters = []

    if date_start:
        filters.append(KsData.publish_date >= date_start)
    if date_stop:
        filters.append(KsData.publish_date <= date_stop)
    if regions:
        filters.append(KsData.region_code.in_(regions))
    if price_range:
        filters.append(KsData.price >= price_range[0])
        filters.append(KsData.price <= price_range[1])

    # Фильтрация данных из таблицы KsData для указанного поставщика
    supplier_data = session.query(KsData).filter(KsData.participant_inn == supplier_inn, *filters).all()

    # Анализ данных для определения топ 5 КПГЗ
    kpgz_counter = Counter(data.kpgz for data in supplier_data)
    top_kpgz = kpgz_counter.most_common(5)

    return top_kpgz


def price_changes_for_supplier(supplier_inn: int, date_start: datetime = None, date_stop: datetime = None,
                    kpgz: str = None, regions: list = None,
                    price_range: list = None):
    if not kpgz:
        return None  # Если КПГЗ не указаны в запросе, возвращаем null

    # Формирование фильтров на основе входных параметров
    filters = []

    if date_start:
        filters.append(KsData.publish_date >= date_start)
    if date_stop:
        filters.append(KsData.publish_date <= date_stop)
    if regions:
        filters.append(KsData.region_code.in_(regions))
    if price_range:
        filters.append(KsData.price >= price_range[0])
        filters.append(KsData.price <= price_range[1])

    # Фильтрация данных из таблицы KsData для указанного поставщика и КПГЗ
    supplier_data = session.query(KsData).filter(
        KsData.participant_inn == supplier_inn,
        KsData.kpgz == kpgz,
        *filters).all()

    # Собираем изменения цен для указанной КПГЗ
    price_changes = []
    for data in supplier_data:
        price_changes.append({'publish_date': data.publish_date, 'price': data.price})

    return price_changes


def market_share_for_supplier(supplier_inn: int, date_start: datetime = None, date_stop: datetime = None,
                    kpgz: str = None, regions: list = None,
                    price_range: list = None):
    if not kpgz:
        return None  # Если КПГЗ не указаны в запросе, возвращаем null

    # Формирование фильтров на основе входных параметров
    filters = []

    if date_start:
        filters.append(KsData.publish_date >= date_start)
    if date_stop:
        filters.append(KsData.publish_date <= date_stop)
    if regions:
        filters.append(KsData.region_code.in_(regions))
    if price_range:
        filters.append(KsData.price >= price_range[0])
        filters.append(KsData.price <= price_range[1])

    # Подсчет доли рынка для указанной КПГЗ
    total_share = session.query(func.count()).filter(*filters).scalar()

    supplier_share = (
        session.query(func.count()).
        filter(
            KsData.participant_inn == supplier_inn,
            KsData.kpgz == kpgz,
            *filters
        ).
        scalar()
    )

    if total_share == 0:
        return 0  # Если общая доля рынка равна нулю, вернуть 0

    # Рассчет доли рынка поставщика
    market_share = (supplier_share / total_share) * 100

    return market_share


def market_share_by_deals(supplier_inn: int, date_start: datetime = None, date_stop: datetime = None,
                    kpgz: str = None, regions: list = None,
                    price_range: list = None):
    if not kpgz:
        return None  # Если КПГЗ не указаны в запросе, возвращаем null

    # Формирование фильтров на основе входных параметров
    filters = []

    if date_start:
        filters.append(ContractsData.conclusion_date >= date_start)
    if date_stop:
        filters.append(ContractsData.conclusion_date <= date_stop)
    if regions:
        filters.append(KsData.region_code.in_(regions))
    if price_range:
        filters.append(ContractsData.price >= price_range[0])
        filters.append(ContractsData.price <= price_range[1])

    # Подсчет количества сделок для указанного поставщика и КПГЗ
    supplier_deals = session.query(func.count()).filter(
        ContractsData.supplier_inn == supplier_inn, ContractsData.kpgz == kpgz, *filters).scalar()

    # Подсчет общего количества сделок для указанной КПГЗ
    total_deals = session.query(func.count()).filter(
        ContractsData.kpgz == kpgz, *filters).scalar()

    if total_deals == 0:
        return 0  # Если общее количество сделок равно нулю, вернуть 0

    # Рассчет доли рынка по количеству сделок
    market_share = (supplier_deals / total_deals) * 100

    return market_share


def compliance_percentage(supplier_inn: int, date_start: datetime = None, date_stop: datetime = None,
                    kpgz: str = None, regions: list = None,
                    price_range: list = None) -> dict:
    # Формирование фильтров на основе входных параметров
    filters = []

    if date_start:
        filters.append(ContractsData.conclusion_date >= date_start)
    if date_stop:
        filters.append(ContractsData.conclusion_date <= date_stop)
    if regions:
        filters.append(KsData.region_code.in_(regions))
    if price_range:
        filters.append(ContractsData.price >= price_range[0])
        filters.append(ContractsData.price <= price_range[1])
    if kpgz:
        filters.append(ContractsData.kpgz == kpgz)

    # Подсчет количества сделок для указанного поставщика и фильтров
    total_deals = session.query(func.count()).filter(
        ContractsData.supplier_inn == supplier_inn, *filters).scalar()

    # Подсчет количества сделок, выполненных в срок для указанного поставщика и фильтров
    on_time_deals = session.query(func.count()).filter(
        ContractsData.supplier_inn == supplier_inn, *filters,
        ContractsData.conclusion_date <= Contract_executionData.scheduled_delivery_date
    ).scalar()

    if total_deals == 0:
        return 0  # Если общее количество сделок равно нулю, вернуть 0

    # Рассчет процента соблюдения сроков
    compliance_percentage = (on_time_deals / total_deals) * 100

    return compliance_percentage


def get_user_rating(supplier_inn: int) -> dict[str, float]:
    count_rep: int  # Кол-во кс
    count_win: int  # Кол-во побед в кс
    date_last_win: datetime  # Последняя дата выигрыша
    count_close: int  # Кол-во завершенных контрактов
    count_block: int  # Кол-во блокировок у поставщика
    date_last_block: int  # Последняя дата блокировки
    mean_days_delay: int  # Среднее время задержки поставки товара, в днях

    count_rep = session.query(func.count()).filter(
        KsData.participant_inn == supplier_inn).scalar()
    count_win = session.query(func.count()).filter(
        KsData.participant_inn == supplier_inn,
        KsData.is_winner == 1).scalar()
    date_last_win = session.query(ContractsData) \
        .filter(ContractsData.supplier_inn == supplier_inn) \
        .order_by(ContractsData.conclusion_date) \
        .first()
    count_close = session.query(func.count()).filter(
        ContractsData.supplier_inn == supplier_inn,
        ContractsData.status == 1).scalar()
    count_block = session.query(func.count()).filter(
        BlockingData.supplier_inn == supplier_inn).scalar()
    date_last_block = session.query(BlockingData) \
        .filter(BlockingData.supplier_inn == supplier_inn) \
        .order_by(BlockingData.blocking_end_date) \
        .first()
    mean_days_delayy = session.query(Contract_executionData) \
        .filter(Contract_executionData.supplier_inn == supplier_inn).all()
    grouped_data = [(data.actual_delivery_date - data.scheduled_delivery_date) for data in mean_days_delayy]
    mean_days_delay = mean(grouped_data)

    k_ban: float | None = 0.03,  # коэффициент регулирующий влияние блокировок
    k_delay: float | None = 0.0004,  # коэффициент регулирующий влияние задержки
    k_active: float | None = 5  # коэффициент уменьшения или снижения рейтинга за активность

    main_rating = (count_close / count_win) * 100  # Подсчет основного рейтинга, в процентах
    ban_rating = np.exp(-k_ban * count_block)  # Подсчет процента основанного на блокировках поставщика
    delay_rating = np.exp(-k_delay * mean_days_delay)  # Подсчет процента основанного на задержках поставок поставщика
    final_rating = main_rating * ban_rating * delay_rating  # Итоговый процент рейтинга для данного поставщика
    time_check = (datetime.today() - datetime.strptime(str(date_last_win), '%m-%d-%Y')).days
    print(time_check)
    time_check_block = (datetime.today() - datetime.strptime(str(date_last_block), '%m-%d-%Y')).days
    if int(time_check) >= 90:
        final_rating - (final_rating / 100 * int(time_check))
    if count_win / count_rep >= 0.7:  # Если процент побед выше 70
        final_rating + (final_rating / 100 * k_active)  # прибавляем к рейтингу 5% от итогового рейтинга
    if int(time_check_block) >= 180:
        final_rating + (final_rating / 100 * k_active)  # прибавляем к рейтингу 5% от итогового рейтинга
    if 0 <= final_rating <= 10:
        stars = 0.5
    elif 10 < final_rating <= 20:
        stars = 1
    elif 20 < final_rating <= 30:
        stars = 1.5
    elif 30 < final_rating <= 40:
        stars = 2
    elif 40 < final_rating <= 50:
        stars = 2.5
    elif 50 < final_rating <= 60:
        stars = 3
    elif 60 < final_rating <= 70:
        stars = 3.5
    elif 70 < final_rating <= 80:
        stars = 4
    elif 80 < final_rating <= 90:
        stars = 4.5
    elif 90 < final_rating <= 100:
        stars = 5
    else:
        stars = 1

    return {"rating": float("{:.2f}".format(final_rating)),
            "stars": float(stars)}


from sqlalchemy import select


# participant_inn


@app.get("/inn_to_payload/{inn}/")
def inn_to_payload(inn: int,
                   date_start: datetime = None,
                   date_stop: datetime = None,
                   kpgz: str = None,
                   regions: str = None,
                   price_range: str = None, ):
    user = select(KsData).where(KsData.customer_inn == inn)
    # ii = session.scalars(user).all()
    if regions:
        regions = str(regions).split(", ")
    if price_range:
        price_range = price_range.split(", ")
    return {"inn": inn,"win_sum":win_sum(inn,
                                                 date_start=date_start,
                                                 date_stop=date_stop,
                                                 kpgz=kpgz,
                                                 price_range=price_range,
                                                 regions=regions),
                                                 "win_sum_by_date":win_sum_by_date(inn,
                                                 date_start=date_start,
                                                 date_stop=date_stop,
                                                 kpgz=kpgz,
                                                 price_range=price_range,
                                                 regions=regions),
                                                  "user_activity": get_user_activity(inn,
                                                 date_start=date_start,
                                                 date_stop=date_stop,
                                                 kpgz=kpgz,
                                                 price_range=price_range,
                                                 regions=regions
                                                 ),
                                                 "user_regions":get_user_regions(inn,
                                                 date_start=date_start,
                                                 date_stop=date_stop,
                                                 kpgz=kpgz,
                                                 price_range=price_range,
                                                 regions=regions),
                                                 "top_kpgz_for_supplier":top_kpgz_for_supplier(inn,
                                                 date_start=date_start,
                                                 date_stop=date_stop,
                                                 kpgz=kpgz,
                                                 price_range=price_range,
                                                 regions=regions),
                                                 "price_changes_for_supplier":price_changes_for_supplier(inn,
                                                 date_start=date_start,
                                                 date_stop=date_stop,
                                                 kpgz=kpgz,
                                                 price_range=price_range,
                                                 regions=regions),
                                                 "market_share_for_supplier":market_share_for_supplier(inn,
                                                 date_start=date_start,
                                                 date_stop=date_stop,
                                                 kpgz=kpgz,
                                                 price_range=price_range,
                                                 regions=regions),
                                                 "market_share_by_deals":market_share_by_deals(inn,date_start=date_start,
                                                 date_stop=date_stop,
                                                 kpgz=kpgz,
                                                 price_range=price_range,
                                                 regions=regions),
                                                 "compliance_percentage":compliance_percentage(inn,
                                                 date_start=date_start,
                                                 date_stop=date_stop,
                                                 kpgz=kpgz,
                                                 price_range=price_range,
                                                 regions=regions)
}
