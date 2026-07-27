#include "assets/json.h"

#include <charconv>
#include <cmath>
#include <cstddef>
#include <cstdint>
#include <limits>
#include <stdexcept>
#include <utility>

namespace mars::assets
{
namespace
{
class JsonParser final
{
public:
    explicit JsonParser(const std::string_view source)
        : source_(source)
    {
        if (source_.size() > 16U * 1024U * 1024U)
        {
            throw std::runtime_error("JSON source exceeds the supported size limit");
        }
    }

    JsonValue Parse()
    {
        SkipWhitespace();
        JsonValue value = ParseValue(0);
        SkipWhitespace();
        if (position_ != source_.size())
        {
            throw Error("Unexpected trailing JSON content");
        }
        return value;
    }

private:
    static constexpr std::size_t kMaximumDepth = 128;

    [[nodiscard]] std::runtime_error Error(const std::string_view message) const
    {
        return std::runtime_error(
            std::string(message) + " at byte " + std::to_string(position_));
    }

    void SkipWhitespace() noexcept
    {
        while (position_ < source_.size())
        {
            const char value = source_[position_];
            if (value != ' ' && value != '\t' && value != '\r' && value != '\n')
            {
                break;
            }
            ++position_;
        }
    }

    [[nodiscard]] char Peek() const
    {
        if (position_ >= source_.size())
        {
            throw Error("Unexpected end of JSON");
        }
        return source_[position_];
    }

    char Take()
    {
        const char value = Peek();
        ++position_;
        return value;
    }

    void Expect(const char expected)
    {
        if (Take() != expected)
        {
            throw Error("Unexpected JSON token");
        }
    }

    JsonValue ParseValue(const std::size_t depth)
    {
        if (depth > kMaximumDepth)
        {
            throw Error("JSON nesting exceeds the supported depth");
        }
        const char value = Peek();
        if (value == 'n')
        {
            ParseLiteral("null");
            return JsonValue{};
        }
        if (value == 't')
        {
            ParseLiteral("true");
            return JsonValue(true);
        }
        if (value == 'f')
        {
            ParseLiteral("false");
            return JsonValue(false);
        }
        if (value == '"')
        {
            return JsonValue(ParseString());
        }
        if (value == '[')
        {
            return JsonValue(ParseArray(depth + 1));
        }
        if (value == '{')
        {
            return JsonValue(ParseObject(depth + 1));
        }
        if (value == '-' || (value >= '0' && value <= '9'))
        {
            return JsonValue(ParseNumber());
        }
        throw Error("Unsupported JSON token");
    }

    void ParseLiteral(const std::string_view literal)
    {
        if (source_.substr(position_, literal.size()) != literal)
        {
            throw Error("Malformed JSON literal");
        }
        position_ += literal.size();
    }

    static std::uint32_t HexValue(const char value)
    {
        if (value >= '0' && value <= '9')
        {
            return static_cast<std::uint32_t>(value - '0');
        }
        if (value >= 'a' && value <= 'f')
        {
            return static_cast<std::uint32_t>(value - 'a' + 10);
        }
        if (value >= 'A' && value <= 'F')
        {
            return static_cast<std::uint32_t>(value - 'A' + 10);
        }
        throw std::runtime_error("Malformed JSON Unicode escape");
    }

    std::uint32_t ParseUnicodeUnit()
    {
        std::uint32_t value = 0;
        for (std::uint32_t index = 0; index < 4; ++index)
        {
            value = (value << 4U) | HexValue(Take());
        }
        return value;
    }

    static void AppendUtf8(std::string& output, const std::uint32_t code_point)
    {
        if (code_point <= 0x7FU)
        {
            output.push_back(static_cast<char>(code_point));
        }
        else if (code_point <= 0x7FFU)
        {
            output.push_back(static_cast<char>(0xC0U | (code_point >> 6U)));
            output.push_back(static_cast<char>(0x80U | (code_point & 0x3FU)));
        }
        else if (code_point <= 0xFFFFU)
        {
            output.push_back(static_cast<char>(0xE0U | (code_point >> 12U)));
            output.push_back(static_cast<char>(0x80U | ((code_point >> 6U) & 0x3FU)));
            output.push_back(static_cast<char>(0x80U | (code_point & 0x3FU)));
        }
        else if (code_point <= 0x10FFFFU)
        {
            output.push_back(static_cast<char>(0xF0U | (code_point >> 18U)));
            output.push_back(static_cast<char>(0x80U | ((code_point >> 12U) & 0x3FU)));
            output.push_back(static_cast<char>(0x80U | ((code_point >> 6U) & 0x3FU)));
            output.push_back(static_cast<char>(0x80U | (code_point & 0x3FU)));
        }
        else
        {
            throw std::runtime_error("JSON Unicode code point is out of range");
        }
    }

    std::string ParseString()
    {
        Expect('"');
        std::string output;
        while (true)
        {
            const char value = Take();
            if (value == '"')
            {
                return output;
            }
            if (static_cast<unsigned char>(value) < 0x20U)
            {
                throw Error("JSON strings cannot contain control bytes");
            }
            if (value != '\\')
            {
                output.push_back(value);
                continue;
            }

            const char escape = Take();
            switch (escape)
            {
            case '"': output.push_back('"'); break;
            case '\\': output.push_back('\\'); break;
            case '/': output.push_back('/'); break;
            case 'b': output.push_back('\b'); break;
            case 'f': output.push_back('\f'); break;
            case 'n': output.push_back('\n'); break;
            case 'r': output.push_back('\r'); break;
            case 't': output.push_back('\t'); break;
            case 'u':
            {
                std::uint32_t code_point = ParseUnicodeUnit();
                if (code_point >= 0xD800U && code_point <= 0xDBFFU)
                {
                    if (Take() != '\\' || Take() != 'u')
                    {
                        throw Error("JSON high surrogate lacks a low surrogate");
                    }
                    const std::uint32_t low = ParseUnicodeUnit();
                    if (low < 0xDC00U || low > 0xDFFFU)
                    {
                        throw Error("JSON low surrogate is invalid");
                    }
                    code_point = 0x10000U + ((code_point - 0xD800U) << 10U)
                        + (low - 0xDC00U);
                }
                else if (code_point >= 0xDC00U && code_point <= 0xDFFFU)
                {
                    throw Error("JSON contains an unpaired low surrogate");
                }
                AppendUtf8(output, code_point);
                break;
            }
            default:
                throw Error("Unsupported JSON escape sequence");
            }
        }
    }

    double ParseNumber()
    {
        const std::size_t start = position_;
        if (Peek() == '-')
        {
            ++position_;
        }
        if (Peek() == '0')
        {
            ++position_;
            if (position_ < source_.size() && source_[position_] >= '0' && source_[position_] <= '9')
            {
                throw Error("JSON numbers cannot contain leading zeroes");
            }
        }
        else
        {
            if (Peek() < '1' || Peek() > '9')
            {
                throw Error("Malformed JSON number");
            }
            while (position_ < source_.size() && source_[position_] >= '0' && source_[position_] <= '9')
            {
                ++position_;
            }
        }
        if (position_ < source_.size() && source_[position_] == '.')
        {
            ++position_;
            const std::size_t fractional_start = position_;
            while (position_ < source_.size() && source_[position_] >= '0' && source_[position_] <= '9')
            {
                ++position_;
            }
            if (position_ == fractional_start)
            {
                throw Error("JSON fractional component is empty");
            }
        }
        if (position_ < source_.size() && (source_[position_] == 'e' || source_[position_] == 'E'))
        {
            ++position_;
            if (position_ < source_.size() && (source_[position_] == '+' || source_[position_] == '-'))
            {
                ++position_;
            }
            const std::size_t exponent_start = position_;
            while (position_ < source_.size() && source_[position_] >= '0' && source_[position_] <= '9')
            {
                ++position_;
            }
            if (position_ == exponent_start)
            {
                throw Error("JSON exponent is empty");
            }
        }

        double value = 0.0;
        const char* begin = source_.data() + start;
        const char* end = source_.data() + position_;
        const auto result = std::from_chars(begin, end, value, std::chars_format::general);
        if (result.ec != std::errc{} || result.ptr != end || !std::isfinite(value))
        {
            throw Error("JSON number is not finite or representable");
        }
        return value;
    }

    JsonValue::Array ParseArray(const std::size_t depth)
    {
        Expect('[');
        SkipWhitespace();
        JsonValue::Array array;
        if (Peek() == ']')
        {
            ++position_;
            return array;
        }
        while (true)
        {
            array.push_back(ParseValue(depth));
            SkipWhitespace();
            const char delimiter = Take();
            if (delimiter == ']')
            {
                return array;
            }
            if (delimiter != ',')
            {
                throw Error("JSON array delimiter is invalid");
            }
            SkipWhitespace();
        }
    }

    JsonValue::Object ParseObject(const std::size_t depth)
    {
        Expect('{');
        SkipWhitespace();
        JsonValue::Object object;
        if (Peek() == '}')
        {
            ++position_;
            return object;
        }
        while (true)
        {
            if (Peek() != '"')
            {
                throw Error("JSON object keys must be strings");
            }
            std::string key = ParseString();
            SkipWhitespace();
            Expect(':');
            SkipWhitespace();
            JsonValue value = ParseValue(depth);
            if (!object.emplace(std::move(key), std::move(value)).second)
            {
                throw Error("JSON object contains a duplicate key");
            }
            SkipWhitespace();
            const char delimiter = Take();
            if (delimiter == '}')
            {
                return object;
            }
            if (delimiter != ',')
            {
                throw Error("JSON object delimiter is invalid");
            }
            SkipWhitespace();
        }
    }

    std::string_view source_{};
    std::size_t position_ = 0;
};

[[noreturn]] void ThrowTypeError(const std::string_view expected)
{
    throw std::runtime_error("JSON value is not a " + std::string(expected));
}
} // namespace

JsonValue::JsonValue(const bool value)
    : type_(Type::Boolean), boolean_(value)
{
}

JsonValue::JsonValue(const double value)
    : type_(Type::Number), number_(value)
{
}

JsonValue::JsonValue(std::string value)
    : type_(Type::String), string_(std::move(value))
{
}

JsonValue::JsonValue(Array value)
    : type_(Type::Array), array_(std::move(value))
{
}

JsonValue::JsonValue(Object value)
    : type_(Type::Object), object_(std::move(value))
{
}

JsonValue::Type JsonValue::GetType() const noexcept
{
    return type_;
}

bool JsonValue::AsBoolean() const
{
    if (type_ != Type::Boolean)
    {
        ThrowTypeError("boolean");
    }
    return boolean_;
}

double JsonValue::AsNumber() const
{
    if (type_ != Type::Number)
    {
        ThrowTypeError("number");
    }
    return number_;
}

const std::string& JsonValue::AsString() const &
{
    if (type_ != Type::String)
    {
        ThrowTypeError("string");
    }
    return string_;
}

std::string JsonValue::AsString() &&
{
    if (type_ != Type::String)
    {
        ThrowTypeError("string");
    }
    return std::move(string_);
}

const JsonValue::Array& JsonValue::AsArray() const &
{
    if (type_ != Type::Array)
    {
        ThrowTypeError("array");
    }
    return array_;
}

JsonValue::Array JsonValue::AsArray() &&
{
    if (type_ != Type::Array)
    {
        ThrowTypeError("array");
    }
    return std::move(array_);
}

const JsonValue::Object& JsonValue::AsObject() const &
{
    if (type_ != Type::Object)
    {
        ThrowTypeError("object");
    }
    return object_;
}

JsonValue::Object JsonValue::AsObject() &&
{
    if (type_ != Type::Object)
    {
        ThrowTypeError("object");
    }
    return std::move(object_);
}

JsonValue ParseJson(const std::string_view source)
{
    return JsonParser(source).Parse();
}

const JsonValue& RequireJsonMember(
    const JsonValue::Object& object,
    const std::string_view name)
{
    const auto found = object.find(name);
    if (found == object.end())
    {
        throw std::runtime_error("Required JSON member is missing: " + std::string(name));
    }
    return found->second;
}

const JsonValue* FindJsonMember(
    const JsonValue::Object& object,
    const std::string_view name) noexcept
{
    const auto found = object.find(name);
    return found == object.end() ? nullptr : &found->second;
}
} // namespace mars::assets
