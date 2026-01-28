"""Custom template filters for documentation app."""

from django import template

register = template.Library()


@register.filter(name='replace')
def replace(value, arg):
    """
    Replace occurrences of a substring in a string.
    
    Supports two syntaxes:
    1. {{ value|replace:"old,new" }} - comma-separated
    2. {{ value|replace:"old":"new" }} - Django-style (requires custom tag)
    
    For Django-style, use: {{ value|replace_:"_":" " }}
    """
    if not value:
        return value
    
    if not arg:
        return value
    
    # Handle comma-separated format: "old,new"
    if ',' in arg:
        old, new = arg.split(',', 1)
        return str(value).replace(old, new)
    
    # If no comma, return as-is (might be used with replace_ tag)
    return str(value)


@register.simple_tag(name='replace_')
def replace_tag(value, old_str, new_str):
    """
    Template tag version of replace that accepts two separate arguments.
    
    Usage: {% replace_ value "_" " " %}
    """
    if not value:
        return value
    return str(value).replace(old_str, new_str)
