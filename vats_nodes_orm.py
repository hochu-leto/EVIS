from sqlalchemy import create_engine,Integer, String, Column, ForeignKey

from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

# engine = create_engine("postgresql+psycopg2://postgres:1111@localhost/sqlalchemy_tuts")

engine = create_engine('sqlite://')  # Create the database in memory
Session = sessionmaker(engine)
session = Session()
Base = declarative_base()


class VATS_N1(Base):
    __tablename__ = 'vats'
    id = Column(Integer(), primary_key=True)
    vats_id = Column(Integer(), unique=True)
    vmu = Column(Integer, ForeignKey('node.id'), nullable=False)
    dc = Column(Integer, ForeignKey('node.id'), nullable=True)
    tdcu  = Column(Integer, ForeignKey('node.id'), nullable=True)
    fpsc  = Column(Integer, ForeignKey('node.id'), nullable=True)
    rpsc  = Column(Integer, ForeignKey('node.id'), nullable=True)   #
    tb  = Column(Integer, ForeignKey('node.id'), nullable=True)

class EvoNode(Base):
    __tablename__ = 'node'
    id = Column(Integer(), primary_key=True)
    node = Column(Integer, ForeignKey('node_name.id'))
    made_in = Column(Integer, ForeignKey('manufacturer.id'))
    type = Column(String(256), nullable=True)
    software = Column(String(100), nullable=True)
    revision = Column(String(100), nullable=True)
    serial_number = Column(String(100), nullable=False)


class Manufacturer(Base):
    __tablename__ = 'manufacturer'
    id = Column(Integer(), primary_key=True)
    name = Column(String(100), nullable=False)


class NodeName(Base):
    __tablename__ = 'node_name'
    id = Column(Integer(), primary_key=True)
    name = Column(String(100), nullable=False)

Base.metadata.create_all(engine)

china_manuf = Manufacturer(name='CHINA')
evocargo_manuf = Manufacturer(name='Evocargo')
BURR_manuf = Manufacturer(name='Мехатроника')
ttc_manuf = Manufacturer(name='ТТС')
smart_manuf = Manufacturer(name='Цикл+')
session.bulk_save_objects([china_manuf, evocargo_manuf, BURR_manuf, ttc_manuf, smart_manuf])

dc_name = NodeName(name='Двигатель(drive_motor)')
tdcu_name = NodeName(name='Инвертор(traction_drive_control_unit)')
vmu_name = NodeName(name='Контроллер Верхнего Уровня')
fpsc_name = NodeName(name='Блок Управления Рулевой Рейкой перед(Front_Power_Steering_Control)')
rpsc_name = NodeName(name='Блок Управления Рулевой Рейкой зад(Rear_Power_Steering_Control)')
tb_name = NodeName(name='Тяговая аккумуляторная батарея')

session.bulk_save_objects([dc_name, tdcu_name, vmu_name, fpsc_name, rpsc_name, tb_name])


vats_51 = VATS_N1(
    vats_id=51,
    vmu=EvoNode(
        node=vmu_name,
        made_in=ttc_manuf,
        software='1.5.3',
        serial_number='05224210000108'
    ).id)

session.add(vats_51)
session.commit()

result = session.query(VATS_N1).all()
print(result[0].vmu.name)