"""
Data validation utilities for API endpoints.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple, Callable
from django.http import JsonResponse

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom exception for validation errors."""
    def __init__(self, message: str, errors: Optional[Dict[str, List[str]]] = None):
        self.message = message
        self.errors = errors or {}
        super().__init__(self.message)


class DataValidator:
    """
    Utility class for validating API request data.
    """
    
    @staticmethod
    def validate_required_fields(
        data: Dict[str, Any],
        required_fields: List[str]
    ) -> Tuple[bool, Optional[Dict[str, List[str]]]]:
        """
        Validate that required fields are present.
        
        Args:
            data: Data dictionary to validate
            required_fields: List of required field names
            
        Returns:
            Tuple of (is_valid, errors_dict)
        """
        errors = {}
        missing_fields = []
        
        for field in required_fields:
            if field not in data or data[field] is None or data[field] == '':
                missing_fields.append(field)
        
        if missing_fields:
            errors['required'] = [f"Missing required field: {field}" for field in missing_fields]
            return False, errors
        
        return True, None
    
    @staticmethod
    def validate_field_types(
        data: Dict[str, Any],
        field_types: Dict[str, type]
    ) -> Tuple[bool, Optional[Dict[str, List[str]]]]:
        """
        Validate field types.
        
        Args:
            data: Data dictionary to validate
            field_types: Dictionary mapping field names to expected types
            
        Returns:
            Tuple of (is_valid, errors_dict)
        """
        errors = {}
        type_errors = []
        
        for field, expected_type in field_types.items():
            if field in data and data[field] is not None:
                if not isinstance(data[field], expected_type):
                    type_errors.append(
                        f"Field '{field}' must be of type {expected_type.__name__}, "
                        f"got {type(data[field]).__name__}"
                    )
        
        if type_errors:
            errors['type'] = type_errors
            return False, errors
        
        return True, None
    
    @staticmethod
    def validate_string_length(
        data: Dict[str, Any],
        field_lengths: Dict[str, Tuple[int, Optional[int]]]
    ) -> Tuple[bool, Optional[Dict[str, List[str]]]]:
        """
        Validate string field lengths.
        
        Args:
            data: Data dictionary to validate
            field_lengths: Dictionary mapping field names to (min_length, max_length) tuples
            
        Returns:
            Tuple of (is_valid, errors_dict)
        """
        errors = {}
        length_errors = []
        
        for field, (min_len, max_len) in field_lengths.items():
            if field in data and data[field] is not None:
                value = str(data[field])
                if min_len is not None and len(value) < min_len:
                    length_errors.append(
                        f"Field '{field}' must be at least {min_len} characters"
                    )
                if max_len is not None and len(value) > max_len:
                    length_errors.append(
                        f"Field '{field}' must be at most {max_len} characters"
                    )
        
        if length_errors:
            errors['length'] = length_errors
            return False, errors
        
        return True, None
    
    @staticmethod
    def validate_choices(
        data: Dict[str, Any],
        field_choices: Dict[str, List[Any]]
    ) -> Tuple[bool, Optional[Dict[str, List[str]]]]:
        """
        Validate that field values are in allowed choices.
        
        Args:
            data: Data dictionary to validate
            field_choices: Dictionary mapping field names to lists of allowed values
            
        Returns:
            Tuple of (is_valid, errors_dict)
        """
        errors = {}
        choice_errors = []
        
        for field, allowed_values in field_choices.items():
            if field in data and data[field] is not None:
                if data[field] not in allowed_values:
                    choice_errors.append(
                        f"Field '{field}' must be one of {allowed_values}, "
                        f"got {data[field]}"
                    )
        
        if choice_errors:
            errors['choice'] = choice_errors
            return False, errors
        
        return True, None
    
    @staticmethod
    def validate_all(
        data: Dict[str, Any],
        required_fields: Optional[List[str]] = None,
        field_types: Optional[Dict[str, type]] = None,
        field_lengths: Optional[Dict[str, Tuple[int, Optional[int]]]] = None,
        field_choices: Optional[Dict[str, List[Any]]] = None,
        custom_validators: Optional[List[Callable[[Dict[str, Any]], Tuple[bool, Optional[str]]]]] = None
    ) -> Tuple[bool, Optional[Dict[str, List[str]]]]:
        """
        Run all validation checks.
        
        Args:
            data: Data dictionary to validate
            required_fields: Optional list of required fields
            field_types: Optional dictionary of field type validations
            field_lengths: Optional dictionary of field length validations
            field_choices: Optional dictionary of field choice validations
            custom_validators: Optional list of custom validator functions
            
        Returns:
            Tuple of (is_valid, errors_dict)
        """
        all_errors = {}
        
        # Required fields
        if required_fields:
            is_valid, errors = DataValidator.validate_required_fields(data, required_fields)
            if not is_valid:
                all_errors.update(errors)
        
        # Field types
        if field_types:
            is_valid, errors = DataValidator.validate_field_types(data, field_types)
            if not is_valid:
                all_errors.update(errors)
        
        # String lengths
        if field_lengths:
            is_valid, errors = DataValidator.validate_string_length(data, field_lengths)
            if not is_valid:
                all_errors.update(errors)
        
        # Choices
        if field_choices:
            is_valid, errors = DataValidator.validate_choices(data, field_choices)
            if not is_valid:
                all_errors.update(errors)
        
        # Custom validators
        if custom_validators:
            for validator in custom_validators:
                is_valid, error_msg = validator(data)
                if not is_valid:
                    if 'custom' not in all_errors:
                        all_errors['custom'] = []
                    all_errors['custom'].append(error_msg)
        
        if all_errors:
            return False, all_errors
        
        return True, None
    
    @staticmethod
    def validation_error_response(
        errors: Dict[str, List[str]],
        message: str = "Validation failed"
    ) -> JsonResponse:
        """
        Create a JSON response for validation errors.
        
        Args:
            errors: Dictionary of validation errors
            message: Error message
            
        Returns:
            JsonResponse with validation errors
        """
        return JsonResponse({
            'success': False,
            'error': message,
            'errors': errors
        }, status=400)
