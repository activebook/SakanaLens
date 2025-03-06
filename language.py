import re

"""
Extracts and cleans English text from a given string, retaining only English characters, numbers, and basic punctuation.

Parameters:
text (str): The input string from which English text is to be extracted.

Returns:
str: The cleaned English text with excess whitespace removed.
"""
def keep_english_only(text):
    # This pattern matches English characters, numbers, punctuation and spaces
    english_pattern = re.compile(r'[a-zA-Z0-9\s.,!?;:\'\"()-]+')
    
    # Find all English text matches
    english_parts = english_pattern.findall(text)
    
    # Join the English parts with spaces
    result = ' '.join(english_parts).strip()
    
    # Clean up any excess whitespace
    result = re.sub(r'\s+', ' ', result)
    
    return result

"""
Extracts and returns only the Chinese characters from the given string.

This function uses regular expressions to identify and extract ranges of Chinese characters from the input text.
It effectively removes any characters that are not Chinese, including punctuation and numbers.

Parameters:
text (str): The input string from which Chinese characters are to be extracted.

Returns:
str: A string containing only the Chinese characters found in the input text.
"""
def keep_chinese_only(text):
    # This pattern matches Chinese characters
    # Includes most common Chinese character ranges
    chinese_pattern = re.compile(r'[\u4e00-\u9fff\u3400-\u4dbf\u20000-\u2a6df\u2a700-\u2b73f\u2b740-\u2b81f\u2b820-\u2ceaf]+')
    
    # Find all continuous sequences of Chinese characters in the text
    chinese_parts = chinese_pattern.findall(text)
    
    # Join the found Chinese character sequences with spaces and remove leading/trailing whitespace
    result = ' '.join(chinese_parts).strip()
    
    # Return the processed string containing only Chinese characters
    return result


"""
Extracts and returns only the Japanese text from the input string.

This function uses regular expressions to identify and extract Hiragana, Katakana, and Kanji characters from the input text.
Characters outside these ranges are ignored.

Parameters:
text (str): The input string, which may contain Japanese and non-Japanese characters.

Returns:
str: A string containing only the Japanese characters found in the input text.
"""
def keep_japanese_only(text):
    # This pattern matches Japanese characters
    # Includes Hiragana, Katakana, and Kanji
    japanese_pattern = re.compile(r'[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9faf\uff66-\uff9f]+')
    
    # Find all strings that match the Japanese character pattern
    japanese_parts = japanese_pattern.findall(text)
    
    # Join the found Japanese character strings and remove leading and trailing whitespace
    result = ' '.join(japanese_parts).strip()
    
    # Return the processed string containing only Japanese characters
    return result


"""
Filter the input text to retain only characters of a specified language.

Parameters:
    text (str): The input text to be filtered.
    lang_type (str): The language type to filter by. Accepts "english", "en", 
                     "chinese", "cn", "japanese", or "jp".

Returns:
    str: A string containing only the characters of the specified language.
         Returns an empty string if the language type is not recognized.
"""
def filter_target_lang(text, lang_type):
    lang_type = lang_type.lower()
    if lang_type == "english" or lang_type == "en" or lang_type == "en-us" or lang_type == "en-gb":
        return keep_english_only(text)
    elif lang_type == "chinese" or lang_type == "cn" or lang_type == "zh" or lang_type == "z":
        return keep_chinese_only(text)
    elif lang_type == "japanese" or lang_type == "jp" or lang_type == "ja" or lang_type == "j":
        return keep_japanese_only(text)
    else:
        return ""


# Testing
if __name__ == "__main__":
    # Example usage
    mixed_text = """Hello world 「もしおれがただ偶然、そしてこうしようというつもりでなくここに立っているのなら、ちょっとばかり絶望するところだな」と、そんなことが彼の頭に思い浮かんだ。 explain this in details:DeepSeek-R1-Zero was trained entirely through reinforcement learning without any supervised fine-tuning data. This approach used RL prompts that included reasoning tasks like math and coding problems, paired with rule-based rewards for accuracy and adherence to specific formatting like <think> and <answer> tags.
but non supervised fine-tuning, without predefined correct answers to the question,sw塞尔达王国之泪终于通关了，花了230小时，掌机做出了3a水平，任天堂确实厉害 how to awards the model to correct answer? English text here 日本語 more English"""
    chinese_only = keep_chinese_only(mixed_text)
    japanese_only = keep_japanese_only(mixed_text)
    english_only = keep_english_only(mixed_text)

    print("English only:", english_only)
    print("Chinese only:", chinese_only)  # Output: "你好 日本語"
    print("Japanese only:", japanese_only)  # Output: "こんにちは 日本語"
