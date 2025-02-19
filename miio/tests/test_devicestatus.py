from enum import Enum

from miio import Device, DeviceStatus
from miio.descriptors import EnumSettingDescriptor, NumberSettingDescriptor
from miio.devicestatus import sensor, setting, switch


def test_multiple():
    class MultipleProperties(DeviceStatus):
        @property
        def first(self):
            return "first"

        @property
        def second(self):
            return "second"

    assert (
        repr(MultipleProperties()) == "<MultipleProperties first=first second=second>"
    )


def test_empty():
    class EmptyStatus(DeviceStatus):
        pass

    assert repr(EmptyStatus() == "<EmptyStatus>")


def test_exception():
    class StatusWithException(DeviceStatus):
        @property
        def raise_exception(self):
            raise Exception("test")

    assert (
        repr(StatusWithException()) == "<StatusWithException raise_exception=Exception>"
    )


def test_inheritance():
    class Parent(DeviceStatus):
        @property
        def from_parent(self):
            return True

    class Child(Parent):
        @property
        def from_child(self):
            return True

    assert repr(Child()) == "<Child from_child=True from_parent=True>"


def test_list():
    class List(DeviceStatus):
        @property
        def return_list(self):
            return [0, 1, 2]

    assert repr(List()) == "<List return_list=[0, 1, 2]>"


def test_none():
    class NoneStatus(DeviceStatus):
        @property
        def return_none(self):
            return None

    assert repr(NoneStatus()) == "<NoneStatus return_none=None>"


def test_sensor_decorator():
    class DecoratedProps(DeviceStatus):
        @property
        @sensor(name="Voltage", unit="V")
        def all_kwargs(self):
            pass

        @property
        @sensor(name="Only name")
        def only_name(self):
            pass

        @property
        @sensor(name="", unknown_kwarg="123")
        def unknown(self):
            pass

    status = DecoratedProps()
    sensors = status.sensors()
    assert len(sensors) == 3

    all_kwargs = sensors["all_kwargs"]
    assert all_kwargs.name == "Voltage"
    assert all_kwargs.unit == "V"

    assert sensors["only_name"].name == "Only name"

    assert "unknown_kwarg" in sensors["unknown"].extras


def test_switch_decorator(mocker):
    class DecoratedSwitches(DeviceStatus):
        @property
        @switch(name="Power", setter_name="set_power")
        def power(self):
            pass

    mocker.patch("miio.Device.send")
    d = Device("127.0.0.1", "68ffffffffffffffffffffffffffffff")

    # Patch status to return our class
    mocker.patch.object(d, "status", return_value=DecoratedSwitches())
    # Patch to create a new setter as defined in the status class
    set_power = mocker.patch.object(d, "set_power", create=True, return_value=1)

    sensors = d.switches()
    assert len(sensors) == 1
    assert sensors["power"].name == "Power"

    sensors["power"].setter(True)
    set_power.assert_called_with(True)


def test_setting_decorator_number(mocker):
    """Tests for setting decorator with numbers."""

    class Settings(DeviceStatus):
        @property
        @setting(
            name="Level",
            unit="something",
            setter_name="set_level",
            min_value=0,
            max_value=2,
        )
        def level(self) -> int:
            return 1

    mocker.patch("miio.Device.send")
    d = Device("127.0.0.1", "68ffffffffffffffffffffffffffffff")

    # Patch status to return our class
    mocker.patch.object(d, "status", return_value=Settings())
    # Patch to create a new setter as defined in the status class
    setter = mocker.patch.object(d, "set_level", create=True)

    settings = d.settings()
    assert len(settings) == 1

    desc = settings["level"]
    assert isinstance(desc, NumberSettingDescriptor)

    assert getattr(d.status(), desc.property) == 1

    assert desc.name == "Level"
    assert desc.min_value == 0
    assert desc.max_value == 2
    assert desc.step == 1

    settings["level"].setter(1)
    setter.assert_called_with(1)


def test_setting_decorator_enum(mocker):
    """Tests for setting decorator with enums."""

    class TestEnum(Enum):
        First = 1
        Second = 2

    class Settings(DeviceStatus):
        @property
        @setting(
            name="Level", unit="something", setter_name="set_level", choices=TestEnum
        )
        def level(self) -> TestEnum:
            return TestEnum.First

    mocker.patch("miio.Device.send")
    d = Device("127.0.0.1", "68ffffffffffffffffffffffffffffff")

    # Patch status to return our class
    mocker.patch.object(d, "status", return_value=Settings())
    # Patch to create a new setter as defined in the status class
    setter = mocker.patch.object(d, "set_level", create=True)

    settings = d.settings()
    assert len(settings) == 1

    desc = settings["level"]
    assert isinstance(desc, EnumSettingDescriptor)
    assert getattr(d.status(), desc.property) == TestEnum.First

    assert desc.name == "Level"
    assert len(desc.choices) == 2

    settings["level"].setter(TestEnum.Second)
    setter.assert_called_with(TestEnum.Second)
