import math
import string

from hypothesis import example, given
from hypothesis.strategies import builds, integers, ip_addresses, one_of, text
import pytest
import voluptuous as vol

from esphome import config_validation
from esphome.components.const import UNIT_FAHRENHEIT
from esphome.components.esp32 import (
    VARIANT_ESP32,
    VARIANT_ESP32C2,
    VARIANT_ESP32C3,
    VARIANT_ESP32C6,
    VARIANT_ESP32H2,
    VARIANT_ESP32S2,
    VARIANT_ESP32S3,
)
from esphome.config_validation import Invalid
from esphome.const import (
    CONF_CURRENT_TEMPERATURE,
    CONF_MAX_TEMPERATURE,
    CONF_MIN_TEMPERATURE,
    CONF_TARGET_TEMPERATURE,
    CONF_TEMPERATURE_STEP,
    CONF_UNIT_OF_MEASUREMENT,
    CONF_VISUAL,
    PLATFORM_BK72XX,
    PLATFORM_ESP32,
    PLATFORM_ESP8266,
    PLATFORM_HOST,
    PLATFORM_LN882X,
    PLATFORM_RP2040,
    PLATFORM_RTL87XX,
    UNIT_CELSIUS,
    UNIT_KELVIN,
)
from esphome.core import CORE, HexInt, Lambda


def test_check_not_templatable__invalid():
    with pytest.raises(Invalid, match="This option is not templatable!"):
        config_validation.check_not_templatable(Lambda(""))


@pytest.mark.parametrize("value", ("foo", 1, "D12", False))
def test_alphanumeric__valid(value):
    actual = config_validation.alphanumeric(value)

    assert actual == str(value)


@pytest.mark.parametrize("value", ("£23", "Foo!"))
def test_alphanumeric__invalid(value):
    with pytest.raises(Invalid):
        config_validation.alphanumeric(value)


@given(value=text(alphabet=string.ascii_lowercase + string.digits + "-_"))
def test_valid_name__valid(value):
    actual = config_validation.valid_name(value)

    assert actual == value


@pytest.mark.parametrize("value", ("foo bar", "FooBar", "foo::bar"))
def test_valid_name__invalid(value):
    with pytest.raises(Invalid):
        config_validation.valid_name(value)


@pytest.mark.parametrize("value", ("${name}", "${NAME}", "$NAME", "${name}_name"))
def test_valid_name__substitution_valid(value):
    CORE.vscode = True
    actual = config_validation.valid_name(value)
    assert actual == value

    CORE.vscode = False
    with pytest.raises(Invalid):
        actual = config_validation.valid_name(value)


@pytest.mark.parametrize("value", ("{NAME}", "${A NAME}"))
def test_valid_name__substitution_like_invalid(value):
    with pytest.raises(Invalid):
        config_validation.valid_name(value)


@pytest.mark.parametrize("value", ("myid", "anID", "SOME_ID_test", "MYID_99"))
def test_validate_id_name__valid(value):
    actual = config_validation.validate_id_name(value)

    assert actual == value


@pytest.mark.parametrize("value", ("id of mine", "id-4", "{name_id}", "id::name"))
def test_validate_id_name__invalid(value):
    with pytest.raises(Invalid):
        config_validation.validate_id_name(value)


@pytest.mark.parametrize("value", ("${id}", "${ID}", "${ID}_test_1", "$MYID"))
def test_validate_id_name__substitution_valid(value):
    CORE.vscode = True
    actual = config_validation.validate_id_name(value)
    assert actual == value

    CORE.vscode = False
    with pytest.raises(Invalid):
        config_validation.validate_id_name(value)


@given(one_of(integers(), text()))
def test_string__valid(value):
    actual = config_validation.string(value)

    assert actual == str(value)


@pytest.mark.parametrize("value", ({}, [], True, False, None))
def test_string__invalid(value):
    with pytest.raises(Invalid):
        config_validation.string(value)


@given(text())
def test_strict_string__valid(value):
    actual = config_validation.string_strict(value)

    assert actual == value


@pytest.mark.parametrize("value", (None, 123))
def test_string_string__invalid(value):
    with pytest.raises(Invalid, match="Must be string, got"):
        config_validation.string_strict(value)


@given(
    builds(
        lambda v: "mdi:" + v,
        text(
            alphabet=string.ascii_letters + string.digits + "-_",
            min_size=1,
            max_size=20,
        ),
    )
)
@example("")
def test_icon__valid(value):
    actual = config_validation.icon(value)

    assert actual == value


def test_icon__invalid():
    with pytest.raises(Invalid, match="Icons must match the format "):
        config_validation.icon("foo")


def test_icon__max_length():
    """Test that icons exceeding 63 bytes are rejected."""
    # Exactly 63 bytes should pass
    max_icon = "mdi:" + "a" * 59  # 63 bytes total
    assert config_validation.icon(max_icon) == max_icon

    # 64 bytes should fail
    too_long = "mdi:" + "a" * 60  # 64 bytes total
    with pytest.raises(Invalid, match="Icon string is too long"):
        config_validation.icon(too_long)


def test_byte_length() -> None:
    """Test ByteLength validator checks UTF-8 byte length, not char count."""
    validator = config_validation.ByteLength(max=10)  # pylint: disable=no-member

    # ASCII: 10 chars = 10 bytes, should pass
    assert validator("a" * 10) == "a" * 10

    # ASCII: 11 chars = 11 bytes, should fail
    with pytest.raises(Invalid, match="too long.*11 bytes.*max 10"):
        validator("a" * 11)

    # Multibyte: 3 chars × 3 bytes = 9 bytes, should pass
    assert validator("温度传") == "温度传"

    # Multibyte: 4 chars × 3 bytes = 12 bytes, should fail
    with pytest.raises(Invalid, match="too long.*12 bytes.*max 10"):
        validator("温度传感")


@pytest.mark.parametrize("value", ("True", "YES", "on", "enAblE", True))
def test_boolean__valid_true(value):
    assert config_validation.boolean(value) is True


@pytest.mark.parametrize("value", ("False", "NO", "off", "disAblE", False))
def test_boolean__valid_false(value):
    assert config_validation.boolean(value) is False


@pytest.mark.parametrize("value", (None, 1, 0, "foo"))
def test_boolean__invalid(value):
    with pytest.raises(Invalid, match="Expected boolean value"):
        config_validation.boolean(value)


@given(value=ip_addresses(v=4).map(str))
def test_ipv4__valid(value):
    config_validation.ipv4address(value)


@pytest.mark.parametrize("value", ("127.0.0", "localhost", ""))
def test_ipv4__invalid(value):
    with pytest.raises(Invalid, match="is not a valid IPv4 address"):
        config_validation.ipv4address(value)


@given(value=ip_addresses(v=6).map(str))
def test_ipv6__valid(value):
    config_validation.ipaddress(value)


@pytest.mark.parametrize("value", ("127.0.0", "localhost", "", "2001:db8::2::3"))
def test_ipv6__invalid(value):
    with pytest.raises(Invalid, match="is not a valid IP address"):
        config_validation.ipaddress(value)


# TODO: ensure_list
@given(integers())
def hex_int__valid(value):
    actual = config_validation.hex_int(value)

    assert isinstance(actual, HexInt)
    assert actual == value


@pytest.mark.parametrize(
    "framework, platform, variant, full, idf, arduino, simple",
    [
        ("arduino", PLATFORM_ESP8266, None, "1", "1", "1", "1"),
        ("arduino", PLATFORM_ESP32, VARIANT_ESP32, "3", "2", "3", "2"),
        ("esp-idf", PLATFORM_ESP32, VARIANT_ESP32, "4", "4", "2", "2"),
        ("arduino", PLATFORM_ESP32, VARIANT_ESP32C2, "3", "2", "3", "2"),
        ("esp-idf", PLATFORM_ESP32, VARIANT_ESP32C2, "4", "4", "2", "2"),
        ("arduino", PLATFORM_ESP32, VARIANT_ESP32S2, "6", "5", "6", "5"),
        ("esp-idf", PLATFORM_ESP32, VARIANT_ESP32S2, "7", "7", "5", "5"),
        ("arduino", PLATFORM_ESP32, VARIANT_ESP32S3, "9", "8", "9", "8"),
        ("esp-idf", PLATFORM_ESP32, VARIANT_ESP32S3, "10", "10", "8", "8"),
        ("arduino", PLATFORM_ESP32, VARIANT_ESP32C3, "12", "11", "12", "11"),
        ("esp-idf", PLATFORM_ESP32, VARIANT_ESP32C3, "13", "13", "11", "11"),
        ("arduino", PLATFORM_ESP32, VARIANT_ESP32C6, "15", "14", "15", "14"),
        ("esp-idf", PLATFORM_ESP32, VARIANT_ESP32C6, "16", "16", "14", "14"),
        ("arduino", PLATFORM_ESP32, VARIANT_ESP32H2, "18", "17", "18", "17"),
        ("esp-idf", PLATFORM_ESP32, VARIANT_ESP32H2, "19", "19", "17", "17"),
        ("arduino", PLATFORM_RP2040, None, "20", "20", "20", "20"),
        ("arduino", PLATFORM_BK72XX, None, "21", "21", "21", "21"),
        ("arduino", PLATFORM_RTL87XX, None, "22", "22", "22", "22"),
        ("arduino", PLATFORM_LN882X, None, "23", "23", "23", "23"),
        ("host", PLATFORM_HOST, None, "24", "24", "24", "24"),
    ],
)
def test_split_default(framework, platform, variant, full, idf, arduino, simple):
    from esphome.components.esp32 import KEY_ESP32
    from esphome.const import (
        KEY_CORE,
        KEY_TARGET_FRAMEWORK,
        KEY_TARGET_PLATFORM,
        KEY_VARIANT,
    )

    CORE.data[KEY_CORE] = {}
    CORE.data[KEY_CORE][KEY_TARGET_PLATFORM] = platform
    CORE.data[KEY_CORE][KEY_TARGET_FRAMEWORK] = framework
    if platform == PLATFORM_ESP32:
        CORE.data[KEY_ESP32] = {}
        CORE.data[KEY_ESP32][KEY_VARIANT] = variant

    common_mappings = {
        "esp8266": "1",
        "esp32": "2",
        "esp32_s2": "5",
        "esp32_s3": "8",
        "esp32_c3": "11",
        "esp32_c6": "14",
        "esp32_h2": "17",
        "rp2040": "20",
        "bk72xx": "21",
        "rtl87xx": "22",
        "ln882x": "23",
        "host": "24",
    }

    arduino_mappings = {
        "esp32_arduino": "3",
        "esp32_s2_arduino": "6",
        "esp32_s3_arduino": "9",
        "esp32_c3_arduino": "12",
        "esp32_c6_arduino": "15",
        "esp32_h2_arduino": "18",
    }

    idf_mappings = {
        "esp32_idf": "4",
        "esp32_s2_idf": "7",
        "esp32_s3_idf": "10",
        "esp32_c3_idf": "13",
        "esp32_c6_idf": "16",
        "esp32_h2_idf": "19",
    }

    schema = config_validation.Schema(
        {
            config_validation.SplitDefault(
                "full", **common_mappings, **idf_mappings, **arduino_mappings
            ): str,
            config_validation.SplitDefault(
                "idf", **common_mappings, **idf_mappings
            ): str,
            config_validation.SplitDefault(
                "arduino", **common_mappings, **arduino_mappings
            ): str,
            config_validation.SplitDefault("simple", **common_mappings): str,
        }
    )

    assert schema({}).get("full") == full
    assert schema({}).get("idf") == idf
    assert schema({}).get("arduino") == arduino
    assert schema({}).get("simple") == simple


@pytest.mark.parametrize(
    "framework, platform, message",
    [
        ("arduino", PLATFORM_ESP32, "ESP32 using arduino framework"),
        ("esp-idf", PLATFORM_ESP32, "ESP32 using esp-idf framework"),
        ("arduino", PLATFORM_ESP8266, "ESP8266 using arduino framework"),
        ("arduino", PLATFORM_RP2040, "RP2040 using arduino framework"),
        ("arduino", PLATFORM_BK72XX, "BK72XX using arduino framework"),
        ("host", PLATFORM_HOST, "HOST using host framework"),
    ],
)
def test_require_framework_version(framework, platform, message):
    from esphome.const import (
        KEY_CORE,
        KEY_FRAMEWORK_VERSION,
        KEY_TARGET_FRAMEWORK,
        KEY_TARGET_PLATFORM,
    )

    CORE.data[KEY_CORE] = {}
    CORE.data[KEY_CORE][KEY_TARGET_PLATFORM] = platform
    CORE.data[KEY_CORE][KEY_TARGET_FRAMEWORK] = framework
    CORE.data[KEY_CORE][KEY_FRAMEWORK_VERSION] = config_validation.Version(1, 0, 0)

    assert (
        config_validation.require_framework_version(
            esp_idf=config_validation.Version(0, 5, 0),
            esp32_arduino=config_validation.Version(0, 5, 0),
            esp8266_arduino=config_validation.Version(0, 5, 0),
            rp2040_arduino=config_validation.Version(0, 5, 0),
            bk72xx_arduino=config_validation.Version(0, 5, 0),
            host=config_validation.Version(0, 5, 0),
            extra_message="test 1",
        )("test")
        == "test"
    )

    with pytest.raises(
        vol.error.Invalid,
        match="This feature requires at least framework version 2.0.0. test 2",
    ):
        config_validation.require_framework_version(
            esp_idf=config_validation.Version(2, 0, 0),
            esp32_arduino=config_validation.Version(2, 0, 0),
            esp8266_arduino=config_validation.Version(2, 0, 0),
            rp2040_arduino=config_validation.Version(2, 0, 0),
            bk72xx_arduino=config_validation.Version(2, 0, 0),
            host=config_validation.Version(2, 0, 0),
            extra_message="test 2",
        )("test")

    assert (
        config_validation.require_framework_version(
            esp_idf=config_validation.Version(1, 5, 0),
            esp32_arduino=config_validation.Version(1, 5, 0),
            esp8266_arduino=config_validation.Version(1, 5, 0),
            rp2040_arduino=config_validation.Version(1, 5, 0),
            bk72xx_arduino=config_validation.Version(1, 5, 0),
            host=config_validation.Version(1, 5, 0),
            max_version=True,
            extra_message="test 3",
        )("test")
        == "test"
    )

    with pytest.raises(
        vol.error.Invalid,
        match="This feature requires framework version 0.5.0 or lower. test 4",
    ):
        config_validation.require_framework_version(
            esp_idf=config_validation.Version(0, 5, 0),
            esp32_arduino=config_validation.Version(0, 5, 0),
            esp8266_arduino=config_validation.Version(0, 5, 0),
            rp2040_arduino=config_validation.Version(0, 5, 0),
            bk72xx_arduino=config_validation.Version(0, 5, 0),
            host=config_validation.Version(0, 5, 0),
            max_version=True,
            extra_message="test 4",
        )("test")

    with pytest.raises(
        vol.error.Invalid, match=f"This feature is incompatible with {message}. test 5"
    ):
        config_validation.require_framework_version(
            extra_message="test 5",
        )("test")


def test_only_with_single_component_loaded() -> None:
    """Test OnlyWith with single component when component is loaded."""
    CORE.loaded_integrations = {"mqtt"}

    schema = config_validation.Schema(
        {
            config_validation.OnlyWith("mqtt_id", "mqtt", default="test_mqtt"): str,
        }
    )

    result = schema({})
    assert result.get("mqtt_id") == "test_mqtt"


def test_only_with_single_component_not_loaded() -> None:
    """Test OnlyWith with single component when component is not loaded."""
    CORE.loaded_integrations = set()

    schema = config_validation.Schema(
        {
            config_validation.OnlyWith("mqtt_id", "mqtt", default="test_mqtt"): str,
        }
    )

    result = schema({})
    assert "mqtt_id" not in result


def test_only_with_list_all_components_loaded() -> None:
    """Test OnlyWith with list when all components are loaded."""
    CORE.loaded_integrations = {"zigbee", "nrf52"}

    schema = config_validation.Schema(
        {
            config_validation.OnlyWith(
                "zigbee_id", ["zigbee", "nrf52"], default="test_zigbee"
            ): str,
        }
    )

    result = schema({})
    assert result.get("zigbee_id") == "test_zigbee"


def test_only_with_list_partial_components_loaded() -> None:
    """Test OnlyWith with list when only some components are loaded."""
    CORE.loaded_integrations = {"zigbee"}  # Only zigbee, not nrf52

    schema = config_validation.Schema(
        {
            config_validation.OnlyWith(
                "zigbee_id", ["zigbee", "nrf52"], default="test_zigbee"
            ): str,
        }
    )

    result = schema({})
    assert "zigbee_id" not in result


def test_only_with_list_no_components_loaded() -> None:
    """Test OnlyWith with list when no components are loaded."""
    CORE.loaded_integrations = set()

    schema = config_validation.Schema(
        {
            config_validation.OnlyWith(
                "zigbee_id", ["zigbee", "nrf52"], default="test_zigbee"
            ): str,
        }
    )

    result = schema({})
    assert "zigbee_id" not in result


def test_only_with_list_multiple_components() -> None:
    """Test OnlyWith with list requiring three components."""
    CORE.loaded_integrations = {"comp1", "comp2", "comp3"}

    schema = config_validation.Schema(
        {
            config_validation.OnlyWith(
                "test_id", ["comp1", "comp2", "comp3"], default="test_value"
            ): str,
        }
    )

    result = schema({})
    assert result.get("test_id") == "test_value"

    # Test with one missing
    CORE.loaded_integrations = {"comp1", "comp2"}
    result = schema({})
    assert "test_id" not in result


def test_only_with_empty_list() -> None:
    """Test OnlyWith with empty list (edge case)."""
    CORE.loaded_integrations = set()

    schema = config_validation.Schema(
        {
            config_validation.OnlyWith("test_id", [], default="test_value"): str,
        }
    )

    # all([]) returns True, so default should be applied
    result = schema({})
    assert result.get("test_id") == "test_value"


def test_only_with_user_value_overrides_default() -> None:
    """Test OnlyWith respects user-provided values over defaults."""
    CORE.loaded_integrations = {"mqtt"}

    schema = config_validation.Schema(
        {
            config_validation.OnlyWith("mqtt_id", "mqtt", default="default_id"): str,
        }
    )

    result = schema({"mqtt_id": "custom_id"})
    assert result.get("mqtt_id") == "custom_id"


@pytest.mark.parametrize("value", ("hello", "Hello World", "test_name", "温度"))
def test_string_no_slash__valid(value: str) -> None:
    actual = config_validation.string_no_slash(value)
    assert actual == value


@pytest.mark.parametrize(
    ("value", "expected"),
    (
        ("has/slash", "has⁄slash"),
        ("a/b/c", "a⁄b⁄c"),
        ("/leading", "⁄leading"),
        ("trailing/", "trailing⁄"),
    ),
)
def test_string_no_slash__slash_replaced_with_warning(
    value: str, expected: str, caplog: pytest.LogCaptureFixture
) -> None:
    """Test that '/' is auto-replaced with fraction slash and warning is logged."""
    actual = config_validation.string_no_slash(value)
    assert actual == expected
    assert "reserved as a URL path separator" in caplog.text
    assert "will become an error in ESPHome 2026.7.0" in caplog.text


def test_string_no_slash__long_string_allowed() -> None:
    # string_no_slash doesn't enforce length - use cv.Length() separately
    long_value = "x" * 200
    assert config_validation.string_no_slash(long_value) == long_value


def test_string_no_slash__empty() -> None:
    assert config_validation.string_no_slash("") == ""


@pytest.mark.parametrize("value", ("Temperature", "Living Room Light", "温度传感器"))
def test_validate_entity_name__valid(value: str) -> None:
    actual = config_validation._validate_entity_name(value)  # pylint: disable=protected-access
    assert actual == value


def test_validate_entity_name__slash_replaced_with_warning(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that '/' in entity names is auto-replaced with fraction slash."""
    actual = config_validation._validate_entity_name("has/slash")  # pylint: disable=protected-access
    assert actual == "has⁄slash"
    assert "reserved as a URL path separator" in caplog.text


def test_validate_entity_name__max_length() -> None:
    # 120 bytes should pass
    assert config_validation._validate_entity_name("x" * 120) == "x" * 120  # pylint: disable=protected-access

    # 121 bytes should fail
    with pytest.raises(Invalid, match="too long.*121 bytes.*Maximum.*120"):
        config_validation._validate_entity_name("x" * 121)  # pylint: disable=protected-access


def test_validate_entity_name__multibyte_byte_length() -> None:
    # 40 chars of 3-byte UTF-8 = 120 bytes, should pass
    assert config_validation._validate_entity_name("温" * 40) == "温" * 40  # pylint: disable=protected-access

    # 41 chars of 3-byte UTF-8 = 123 bytes, should fail (over 120 byte limit)
    with pytest.raises(Invalid, match="too long.*123 bytes.*Maximum.*120"):
        config_validation._validate_entity_name("温" * 41)  # pylint: disable=protected-access


def test_validate_entity_name__none_without_friendly_name() -> None:
    # When name is "None" and friendly_name is not set, it should fail
    CORE.friendly_name = None
    with pytest.raises(Invalid, match="friendly_name is not set"):
        config_validation._validate_entity_name("None")  # pylint: disable=protected-access


def test_validate_entity_name__none_with_friendly_name() -> None:
    # When name is "None" but friendly_name is set, it should return None
    CORE.friendly_name = "My Device"
    result = config_validation._validate_entity_name("None")  # pylint: disable=protected-access
    assert result is None
    CORE.friendly_name = None  # Reset


# --- percentage validators ---


@pytest.mark.parametrize(
    ("value", "expected"),
    (
        ("0%", 0.0),
        ("50%", 0.5),
        ("100%", 1.0),
        (0.0, 0.0),
        (0.5, 0.5),
        (1.0, 1.0),
        ("0.0", 0.0),
        ("0.5", 0.5),
        ("1.0", 1.0),
    ),
)
def test_percentage__valid(value: object, expected: float) -> None:
    assert config_validation.percentage(value) == expected


@pytest.mark.parametrize(
    "value",
    (
        "150%",
        "-10%",
        "-0.1",
        "1.1",
        2,
        -1,
        "foo",
        None,
    ),
)
def test_percentage__invalid(value: object) -> None:
    with pytest.raises(Invalid):
        config_validation.percentage(value)


@pytest.mark.parametrize(
    ("value", "expected"),
    (
        ("0%", 0.0),
        ("50%", 0.5),
        ("100%", 1.0),
        ("-50%", -0.5),
        ("-100%", -1.0),
        (0.0, 0.0),
        (0.5, 0.5),
        (-0.5, -0.5),
        (1.0, 1.0),
        (-1.0, -1.0),
    ),
)
def test_possibly_negative_percentage__valid(value: object, expected: float) -> None:
    assert config_validation.possibly_negative_percentage(value) == expected


@pytest.mark.parametrize(
    "value",
    (
        "150%",
        "-150%",
        2,
        -2,
        "foo",
        None,
    ),
)
def test_possibly_negative_percentage__invalid(value: object) -> None:
    with pytest.raises(Invalid):
        config_validation.possibly_negative_percentage(value)


@pytest.mark.parametrize(
    ("value", "expected"),
    (
        ("0%", 0.0),
        ("50%", 0.5),
        ("100%", 1.0),
        ("150%", 1.5),
        ("200%", 2.0),
        (0.0, 0.0),
        (0.5, 0.5),
        (1.0, 1.0),
    ),
)
def test_unbounded_percentage__valid(value: object, expected: float) -> None:
    assert config_validation.unbounded_percentage(value) == expected


@pytest.mark.parametrize(
    "value",
    (
        "-10%",
        "-0.5",
        -1,
        "foo",
        None,
    ),
)
def test_unbounded_percentage__invalid(value: object) -> None:
    with pytest.raises(Invalid):
        config_validation.unbounded_percentage(value)


@pytest.mark.parametrize(
    ("value", "expected"),
    (
        ("0%", 0.0),
        ("50%", 0.5),
        ("150%", 1.5),
        ("-50%", -0.5),
        ("-150%", -1.5),
        ("200%", 2.0),
        ("-200%", -2.0),
        (0.0, 0.0),
        (0.5, 0.5),
        (-0.5, -0.5),
        (1.0, 1.0),
        (-1.0, -1.0),
    ),
)
def test_unbounded_possibly_negative_percentage__valid(
    value: object, expected: float
) -> None:
    assert config_validation.unbounded_possibly_negative_percentage(value) == expected


@pytest.mark.parametrize("value", ("foo", None))
def test_unbounded_possibly_negative_percentage__invalid(value: object) -> None:
    with pytest.raises(Invalid):
        config_validation.unbounded_possibly_negative_percentage(value)


@pytest.mark.parametrize(
    "value",
    (50, -50, 2, -2),
)
def test_percentage_validators__raw_number_above_one_without_percent_sign(
    value: object,
) -> None:
    """Raw numeric values outside [-1, 1] must use a percent sign."""
    with pytest.raises(Invalid, match="percent sign"):
        config_validation.unbounded_percentage(value)
    with pytest.raises(Invalid, match="percent sign"):
        config_validation.unbounded_possibly_negative_percentage(value)


# ---------------------------------------------------------------------------
# temperature and temperature_delta
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "value, expected",
    [
        ("0°C", 0.0),
        ("20C", 20.0),
        ("20", 20.0),
        ("373.15K", 100.0),
        ("373.15°K", 100.0),
        ("32°F", 0.0),
        ("212F", 100.0),
    ],
)
def test_temperature__valid(value, expected) -> None:
    assert math.isclose(config_validation.temperature(value), expected, abs_tol=1e-4)


def test_temperature__invalid() -> None:
    with pytest.raises(Invalid):
        config_validation.temperature(None)


@pytest.mark.parametrize(
    "value, expected",
    [
        ("1°C", 1.0),
        ("1C", 1.0),
        ("1", 1.0),
        ("1K", 1.0),
        ("1.8°F", 1.8 * 5 / 9),
    ],
)
def test_temperature_delta__valid(value, expected) -> None:
    assert math.isclose(
        config_validation.temperature_delta(value), expected, abs_tol=1e-4
    )


def test_temperature_delta__invalid() -> None:
    with pytest.raises(Invalid):
        config_validation.temperature_delta(None)


# ---------------------------------------------------------------------------
# temperature_with_unit
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "value, expected_raw, expected_unit",
    [
        ("100°F", 100.0, UNIT_FAHRENHEIT),
        ("100 °F", 100.0, UNIT_FAHRENHEIT),
        ("100F", 100.0, UNIT_FAHRENHEIT),
        ("100°C", 100.0, UNIT_CELSIUS),
        ("100C", 100.0, UNIT_CELSIUS),
        ("373.15K", 373.15, UNIT_KELVIN),
        ("373.15°K", 373.15, UNIT_KELVIN),
        # No unit: raw value returned, unit is None
        ("100", 100.0, None),
        ("100°", 100.0, None),
        (100, 100.0, None),
    ],
)
def test_temperature_with_unit__valid(value, expected_raw, expected_unit) -> None:
    raw, unit = config_validation.temperature_with_unit(value)
    assert math.isclose(raw, expected_raw, rel_tol=1e-6)
    assert unit == expected_unit


@pytest.mark.parametrize("value", ("not_a_number", "abc°F", None))
def test_temperature_with_unit__invalid(value) -> None:
    with pytest.raises(Invalid):
        config_validation.temperature_with_unit(value)


# ---------------------------------------------------------------------------
# visual_temperature_step
# ---------------------------------------------------------------------------


def test_visual_temperature_step__scalar() -> None:
    """A scalar value sets both target and current to the same value."""
    result = config_validation.visual_temperature_step("1°F")
    assert result[CONF_TARGET_TEMPERATURE] == (1.0, UNIT_FAHRENHEIT)
    assert result[CONF_CURRENT_TEMPERATURE] == (1.0, UNIT_FAHRENHEIT)


def test_visual_temperature_step__scalar_no_unit() -> None:
    result = config_validation.visual_temperature_step("0.5")
    assert result[CONF_TARGET_TEMPERATURE] == (0.5, None)
    assert result[CONF_CURRENT_TEMPERATURE] == (0.5, None)


def test_visual_temperature_step__dict_separate_values() -> None:
    result = config_validation.visual_temperature_step(
        {
            CONF_TARGET_TEMPERATURE: "1°F",
            CONF_CURRENT_TEMPERATURE: "0.5°F",
        }
    )
    assert result[CONF_TARGET_TEMPERATURE] == (1.0, UNIT_FAHRENHEIT)
    assert result[CONF_CURRENT_TEMPERATURE] == (0.5, UNIT_FAHRENHEIT)


def test_visual_temperature_step__dict_missing_key_invalid() -> None:
    with pytest.raises(Invalid):
        config_validation.visual_temperature_step({CONF_TARGET_TEMPERATURE: "1°F"})


# ---------------------------------------------------------------------------
# validate_temperature_config
# ---------------------------------------------------------------------------


def _make_config(uom=None, visual=None):
    """Helper to build a minimal config dict for validate_temperature_config."""
    config = {CONF_VISUAL: visual or {}}
    if uom is not None:
        config[CONF_UNIT_OF_MEASUREMENT] = uom
    return config


def test_validate_temperature_config__empty_visual_defaults_to_celsius() -> None:
    """No temperatures and no UOM: UOM defaults to Celsius."""
    result = config_validation.validate_temperature_config(_make_config())
    assert result[CONF_UNIT_OF_MEASUREMENT] == UNIT_CELSIUS


def test_validate_temperature_config__explicit_uom_fahrenheit_no_conversion() -> None:
    """Explicit UOM=°F with °F temps: values stored as-is (no conversion)."""
    config = _make_config(
        uom=UNIT_FAHRENHEIT,
        visual={
            CONF_MIN_TEMPERATURE: (100.0, UNIT_FAHRENHEIT),
            CONF_MAX_TEMPERATURE: (145.0, UNIT_FAHRENHEIT),
        },
    )
    result = config_validation.validate_temperature_config(config)
    assert result[CONF_UNIT_OF_MEASUREMENT] == UNIT_FAHRENHEIT
    assert math.isclose(result[CONF_VISUAL][CONF_MIN_TEMPERATURE], 100.0)
    assert math.isclose(result[CONF_VISUAL][CONF_MAX_TEMPERATURE], 145.0)


def test_validate_temperature_config__explicit_uom_celsius() -> None:
    """Explicit UOM=°C: values stored as-is."""
    config = _make_config(
        uom=UNIT_CELSIUS,
        visual={CONF_MIN_TEMPERATURE: (18.0, UNIT_CELSIUS)},
    )
    result = config_validation.validate_temperature_config(config)
    assert result[CONF_UNIT_OF_MEASUREMENT] == UNIT_CELSIUS
    assert math.isclose(result[CONF_VISUAL][CONF_MIN_TEMPERATURE], 18.0)


def test_validate_temperature_config__explicit_uom_kelvin() -> None:
    """Explicit UOM=K: values stored as-is."""
    config = _make_config(
        uom=UNIT_KELVIN,
        visual={CONF_MIN_TEMPERATURE: (293.15, UNIT_KELVIN)},
    )
    result = config_validation.validate_temperature_config(config)
    assert result[CONF_UNIT_OF_MEASUREMENT] == UNIT_KELVIN
    assert math.isclose(result[CONF_VISUAL][CONF_MIN_TEMPERATURE], 293.15)


def test_validate_temperature_config__implicit_fahrenheit_legacy_conversion() -> None:
    """No explicit UOM but °F suffixes: legacy path converts to Celsius, sets UOM=°C."""
    config = _make_config(
        visual={CONF_MIN_TEMPERATURE: (32.0, UNIT_FAHRENHEIT)},
    )
    result = config_validation.validate_temperature_config(config)
    assert result[CONF_UNIT_OF_MEASUREMENT] == UNIT_CELSIUS
    # 32°F → 0°C
    assert math.isclose(result[CONF_VISUAL][CONF_MIN_TEMPERATURE], 0.0, abs_tol=1e-6)


def test_validate_temperature_config__implicit_kelvin_legacy_conversion() -> None:
    """No explicit UOM but K suffixes: legacy path converts to Celsius, sets UOM=°C."""
    config = _make_config(
        visual={CONF_MIN_TEMPERATURE: (273.15, UNIT_KELVIN)},
    )
    result = config_validation.validate_temperature_config(config)
    assert result[CONF_UNIT_OF_MEASUREMENT] == UNIT_CELSIUS
    # 273.15 K → 0°C
    assert math.isclose(result[CONF_VISUAL][CONF_MIN_TEMPERATURE], 0.0, abs_tol=1e-6)


def test_validate_temperature_config__implicit_celsius_no_conversion() -> None:
    """No explicit UOM, °C suffix: stored as-is, UOM=°C."""
    config = _make_config(
        visual={CONF_MIN_TEMPERATURE: (18.0, UNIT_CELSIUS)},
    )
    result = config_validation.validate_temperature_config(config)
    assert result[CONF_UNIT_OF_MEASUREMENT] == UNIT_CELSIUS
    assert math.isclose(result[CONF_VISUAL][CONF_MIN_TEMPERATURE], 18.0)


def test_validate_temperature_config__no_unit_suffix_defaults_celsius() -> None:
    """Temperature field with no unit suffix: stored as-is, UOM=°C."""
    config = _make_config(
        visual={CONF_MIN_TEMPERATURE: (18.0, None)},
    )
    result = config_validation.validate_temperature_config(config)
    assert result[CONF_UNIT_OF_MEASUREMENT] == UNIT_CELSIUS
    assert math.isclose(result[CONF_VISUAL][CONF_MIN_TEMPERATURE], 18.0)


def test_validate_temperature_config__mixed_units_legacy_converts_independently() -> (
    None
):
    """No UOM with mixed unit suffixes: each field is converted to °C independently."""
    config = _make_config(
        visual={
            CONF_MIN_TEMPERATURE: (18.0, UNIT_CELSIUS),
            CONF_MAX_TEMPERATURE: (86.0, UNIT_FAHRENHEIT),
        },
    )
    result = config_validation.validate_temperature_config(config)
    assert result[CONF_UNIT_OF_MEASUREMENT] == UNIT_CELSIUS
    assert math.isclose(result[CONF_VISUAL][CONF_MIN_TEMPERATURE], 18.0)
    # 86°F → 30°C
    assert math.isclose(result[CONF_VISUAL][CONF_MAX_TEMPERATURE], 30.0, abs_tol=1e-4)


def test_validate_temperature_config__uom_converts_mismatched_field_unit() -> None:
    """Explicit UOM with a field in a different unit: field is converted to the UOM."""
    config = _make_config(
        uom=UNIT_FAHRENHEIT,
        visual={CONF_MIN_TEMPERATURE: (0.0, UNIT_CELSIUS)},
    )
    result = config_validation.validate_temperature_config(config)
    assert result[CONF_UNIT_OF_MEASUREMENT] == UNIT_FAHRENHEIT
    # 0°C → 32°F
    assert math.isclose(result[CONF_VISUAL][CONF_MIN_TEMPERATURE], 32.0, abs_tol=1e-4)


def test_validate_temperature_config__temperature_step_scalar() -> None:
    """Scalar temperature_step (water_heater style) is stored as a plain float."""
    config = _make_config(
        uom=UNIT_FAHRENHEIT,
        visual={CONF_TEMPERATURE_STEP: (1.0, UNIT_FAHRENHEIT)},
    )
    result = config_validation.validate_temperature_config(config)
    assert math.isclose(result[CONF_VISUAL][CONF_TEMPERATURE_STEP], 1.0)


def test_validate_temperature_config__temperature_step_scalar_legacy_conversion() -> (
    None
):
    """Scalar °F step with no UOM (legacy): converted as a relative delta (no offset)."""
    config = _make_config(
        visual={CONF_TEMPERATURE_STEP: (1.0, UNIT_FAHRENHEIT)},
    )
    result = config_validation.validate_temperature_config(config)
    # 1°F delta → 1 * (5/9) °C delta
    assert math.isclose(
        result[CONF_VISUAL][CONF_TEMPERATURE_STEP], 1.0 * 5.0 / 9.0, rel_tol=1e-6
    )


def test_validate_temperature_config__temperature_step_dict_climate_style() -> None:
    """Dict temperature_step (climate style) processes target and current separately."""
    config = _make_config(
        uom=UNIT_FAHRENHEIT,
        visual={
            CONF_TEMPERATURE_STEP: {
                CONF_TARGET_TEMPERATURE: (1.0, UNIT_FAHRENHEIT),
                CONF_CURRENT_TEMPERATURE: (0.5, UNIT_FAHRENHEIT),
            }
        },
    )
    result = config_validation.validate_temperature_config(config)
    step = result[CONF_VISUAL][CONF_TEMPERATURE_STEP]
    assert math.isclose(step[CONF_TARGET_TEMPERATURE], 1.0)
    assert math.isclose(step[CONF_CURRENT_TEMPERATURE], 0.5)


def test_validate_temperature_config__temperature_step_dict_legacy_conversion() -> None:
    """Dict °F step with no UOM (legacy): each sub-value converted as relative delta."""
    config = _make_config(
        visual={
            CONF_TEMPERATURE_STEP: {
                CONF_TARGET_TEMPERATURE: (1.8, UNIT_FAHRENHEIT),
                CONF_CURRENT_TEMPERATURE: (0.9, UNIT_FAHRENHEIT),
            }
        },
    )
    result = config_validation.validate_temperature_config(config)
    step = result[CONF_VISUAL][CONF_TEMPERATURE_STEP]
    assert math.isclose(step[CONF_TARGET_TEMPERATURE], 1.8 * 5.0 / 9.0, rel_tol=1e-6)
    assert math.isclose(step[CONF_CURRENT_TEMPERATURE], 0.9 * 5.0 / 9.0, rel_tol=1e-6)


# ---------------------------------------------------------------------------
# unit_of_measurement
# ---------------------------------------------------------------------------


def test_unit_of_measurement__valid() -> None:
    validator = config_validation.unit_of_measurement(max_length=8)
    assert validator("°C") == "°C"
    assert validator("°F") == "°F"


def test_unit_of_measurement__too_long() -> None:
    validator = config_validation.unit_of_measurement(max_length=4)
    with pytest.raises(Invalid):
        validator("toolong!")


def test_unit_of_measurement__non_string() -> None:
    validator = config_validation.unit_of_measurement(max_length=8)
    with pytest.raises(Invalid):
        validator(42)
