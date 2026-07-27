#pragma once

#include <map>
#include <string>
#include <string_view>
#include <vector>

namespace mars::assets
{
class JsonValue final
{
public:
    enum class Type
    {
        Null,
        Boolean,
        Number,
        String,
        Array,
        Object,
    };

    using Array = std::vector<JsonValue>;
    using Object = std::map<std::string, JsonValue, std::less<>>;

    JsonValue() = default;
    explicit JsonValue(bool value);
    explicit JsonValue(double value);
    explicit JsonValue(std::string value);
    explicit JsonValue(Array value);
    explicit JsonValue(Object value);

    [[nodiscard]] Type GetType() const noexcept;
    [[nodiscard]] bool AsBoolean() const;
    [[nodiscard]] double AsNumber() const;
    [[nodiscard]] const std::string& AsString() const &;
    [[nodiscard]] std::string AsString() &&;
    [[nodiscard]] const Array& AsArray() const &;
    [[nodiscard]] Array AsArray() &&;
    [[nodiscard]] const Object& AsObject() const &;
    [[nodiscard]] Object AsObject() &&;

private:
    Type type_ = Type::Null;
    bool boolean_ = false;
    double number_ = 0.0;
    std::string string_{};
    Array array_{};
    Object object_{};
};

[[nodiscard]] JsonValue ParseJson(std::string_view source);
[[nodiscard]] const JsonValue& RequireJsonMember(
    const JsonValue::Object& object,
    std::string_view name);
[[nodiscard]] const JsonValue* FindJsonMember(
    const JsonValue::Object& object,
    std::string_view name) noexcept;
} // namespace mars::assets
