from langchain_core.tools import tool
from typing import List, Optional, Dict, Any
import math

# 基础数学工具
@tool
def add(a: float, b: float) -> float:
    """
    计算两个数字的和。
    
    参数:
        a: 第一个数字
        b: 第二个数字
    
    返回:
        两个数字的和
    """
    return a + b

@tool
def multiply(a: float, b: float) -> float:
    """
    计算两个数字的乘积。
    
    参数:
        a: 第一个数字
        b: 第二个数字
    
    返回:
        两个数字的乘积
    """
    return a * b

@tool
def subtract(a: float, b: float) -> float:
    """
    计算两个数字的差。
    
    参数:
        a: 第一个数字
        b: 第二个数字
    
    返回:
        a减去b的差
    """
    return a - b

@tool
def divide(a: float, b: float) -> float:
    """
    计算两个数字的商。
    
    参数:
        a: 被除数
        b: 除数 (不能为0)
    
    返回:
        a除以b的商
    """
    if b == 0:
        raise ValueError("除数不能为0")
    return a / b

@tool
def square_root(number: float) -> float:
    """
    计算一个数的平方根。
    
    参数:
        number: 需要计算平方根的数 (必须大于等于0)
    
    返回:
        数字的平方根
    """
    if number < 0:
        raise ValueError("不能计算负数的平方根")
    return math.sqrt(number)

@tool
def power(base: float, exponent: float) -> float:
    """
    计算一个数的幂。
    
    参数:
        base: 底数
        exponent: 指数
    
    返回:
        base的exponent次幂
    """
    return math.pow(base, exponent)

# 字符串处理工具
@tool
def concatenate(strings: List[str], separator: str = "") -> str:
    """
    将多个字符串连接起来。
    
    参数:
        strings: 要连接的字符串列表
        separator: 连接字符串时使用的分隔符，默认为空
    
    返回:
        连接后的字符串
    """
    return separator.join(strings)

@tool
def to_uppercase(text: str) -> str:
    """
    将文本转换为大写。
    
    参数:
        text: 需要转换的文本
    
    返回:
        转换为大写后的文本
    """
    return text.upper()

@tool
def to_lowercase(text: str) -> str:
    """
    将文本转换为小写。
    
    参数:
        text: 需要转换的文本
    
    返回:
        转换为小写后的文本
    """
    return text.lower()

