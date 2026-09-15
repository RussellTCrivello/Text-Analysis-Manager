"""
Data Validation System
Provides validation rules and data quality checks
"""
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
import re
from utils.logger import get_logger

logger = get_logger(__name__)


class ValidationRule:
    """Single validation rule"""
    
    def __init__(self, field: str, rule_type: str, value: Any = None, 
                 message: str = None, validator: Callable = None):
        self.field = field
        self.rule_type = rule_type  # required, min_length, max_length, pattern, custom, etc.
        self.value = value
        self.message = message or f"Validation failed for {field}"
        self.validator = validator
    
    def validate(self, data: Dict) -> tuple[bool, str]:
        """Validate data against this rule"""
        field_value = data.get(self.field)
        
        if self.rule_type == 'required':
            if field_value is None or (isinstance(field_value, str) and not field_value.strip()):
                return False, self.message or f"{self.field} is required"
        
        elif self.rule_type == 'min_length':
            if field_value and len(str(field_value)) < self.value:
                return False, self.message or f"{self.field} must be at least {self.value} characters"
        
        elif self.rule_type == 'max_length':
            if field_value and len(str(field_value)) > self.value:
                return False, self.message or f"{self.field} must be at most {self.value} characters"
        
        elif self.rule_type == 'pattern':
            if field_value and not re.match(self.value, str(field_value)):
                return False, self.message or f"{self.field} format is invalid"
        
        elif self.rule_type == 'min_value':
            try:
                num_value = float(field_value) if field_value else 0
                if num_value < self.value:
                    return False, self.message or f"{self.field} must be at least {self.value}"
            except (ValueError, TypeError):
                return False, self.message or f"{self.field} must be a number"
        
        elif self.rule_type == 'max_value':
            try:
                num_value = float(field_value) if field_value else 0
                if num_value > self.value:
                    return False, self.message or f"{self.field} must be at most {self.value}"
            except (ValueError, TypeError):
                return False, self.message or f"{self.field} must be a number"
        
        elif self.rule_type == 'email':
            if field_value and not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', str(field_value)):
                return False, self.message or f"{self.field} must be a valid email"
        
        elif self.rule_type == 'url':
            if field_value and not re.match(r'^https?://', str(field_value)):
                return False, self.message or f"{self.field} must be a valid URL"
        
        elif self.rule_type == 'date':
            if field_value:
                try:
                    datetime.strptime(str(field_value)[:10], '%Y-%m-%d')
                except ValueError:
                    return False, self.message or f"{self.field} must be a valid date (YYYY-MM-DD)"
        
        elif self.rule_type == 'custom' and self.validator:
            try:
                if not self.validator(field_value, data):
                    return False, self.message
            except Exception as e:
                return False, f"Validation error: {str(e)}"
        
        return True, ""
    
    def to_dict(self) -> Dict:
        """Convert rule to dictionary"""
        return {
            'field': self.field,
            'rule_type': self.rule_type,
            'value': self.value,
            'message': self.message
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ValidationRule':
        """Create rule from dictionary"""
        return cls(
            field=data['field'],
            rule_type=data['rule_type'],
            value=data.get('value'),
            message=data.get('message')
        )


class ValidationSchema:
    """Collection of validation rules for a table"""
    
    def __init__(self, table_name: str):
        self.table_name = table_name
        self.rules: List[ValidationRule] = []
    
    def add_rule(self, rule: ValidationRule):
        """Add a validation rule"""
        self.rules.append(rule)
    
    def validate(self, data: Dict) -> tuple[bool, List[str]]:
        """Validate data against all rules"""
        errors = []
        
        for rule in self.rules:
            is_valid, error_msg = rule.validate(data)
            if not is_valid:
                errors.append(error_msg)
        
        return len(errors) == 0, errors
    
    def get_field_rules(self, field: str) -> List[ValidationRule]:
        """Get all rules for a specific field"""
        return [rule for rule in self.rules if rule.field == field]
    
    def to_dict(self) -> Dict:
        """Convert schema to dictionary"""
        return {
            'table_name': self.table_name,
            'rules': [rule.to_dict() for rule in self.rules]
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ValidationSchema':
        """Create schema from dictionary"""
        schema = cls(data['table_name'])
        for rule_data in data.get('rules', []):
            schema.add_rule(ValidationRule.from_dict(rule_data))
        return schema


class DataValidator:
    """Main data validator class"""
    
    def __init__(self):
        self.schemas: Dict[str, ValidationSchema] = {}
        self.load_default_schemas()
    
    def load_default_schemas(self):
        """Load default validation schemas"""
        # Sources schema
        sources_schema = ValidationSchema('sources')
        sources_schema.add_rule(ValidationRule('name', 'required', message='Source name is required'))
        sources_schema.add_rule(ValidationRule('name', 'min_length', 2, message='Source name must be at least 2 characters'))
        sources_schema.add_rule(ValidationRule('type', 'required', message='Source type is required'))
        sources_schema.add_rule(ValidationRule('link_sources', 'required', message='Source link is required'))
        sources_schema.add_rule(ValidationRule('link_sources', 'url', message='Link must be a valid URL'))
        sources_schema.add_rule(ValidationRule('country', 'required', message='Country is required'))
        sources_schema.add_rule(ValidationRule('importance', 'min_value', 0.0, message='Importance must be between 0 and 1'))
        sources_schema.add_rule(ValidationRule('importance', 'max_value', 1.0, message='Importance must be between 0 and 1'))
        self.schemas['sources'] = sources_schema
        
        # Contents schema
        contents_schema = ValidationSchema('contents')
        # Titles are optional in the persisted schema; content itself is not.
        contents_schema.add_rule(ValidationRule('content_data', 'required', message='Content data is required'))
        contents_schema.add_rule(ValidationRule('sources_id', 'required', message='Source is required'))
        contents_schema.add_rule(ValidationRule('importance', 'min_value', 0.0, message='Importance must be between 0 and 1'))
        contents_schema.add_rule(ValidationRule('importance', 'max_value', 1.0, message='Importance must be between 0 and 1'))
        self.schemas['contents'] = contents_schema
        
        # Analysis schema
        analysis_schema = ValidationSchema('content_analysis')
        analysis_schema.add_rule(ValidationRule('content_id', 'required', message='Content ID is required'))
        analysis_schema.add_rule(ValidationRule('classification', 'min_length', 2, message='Classification must be at least 2 characters'))
        self.schemas['content_analysis'] = analysis_schema
    
    def validate(self, table_name: str, data: Dict) -> tuple[bool, List[str]]:
        """Validate data for a table"""
        if table_name not in self.schemas:
            logger.warning(f"No validation schema for table: {table_name}")
            return True, []
        
        return self.schemas[table_name].validate(data)
    
    def add_schema(self, schema: ValidationSchema):
        """Add or update a validation schema"""
        self.schemas[schema.table_name] = schema
    
    def get_schema(self, table_name: str) -> Optional[ValidationSchema]:
        """Get validation schema for a table"""
        return self.schemas.get(table_name)
    
    def add_rule(self, table_name: str, rule: ValidationRule):
        """Add a rule to a schema"""
        if table_name not in self.schemas:
            self.schemas[table_name] = ValidationSchema(table_name)
        self.schemas[table_name].add_rule(rule)
    
    def validate_batch(self, table_name: str, data_list: List[Dict]) -> Dict[int, List[str]]:
        """Validate a batch of records, returns errors by index"""
        errors = {}
        for idx, data in enumerate(data_list):
            is_valid, error_msgs = self.validate(table_name, data)
            if not is_valid:
                errors[idx] = error_msgs
        return errors


# Global validator instance
_validator = None

def get_validator() -> DataValidator:
    """Get global validator instance"""
    global _validator
    if _validator is None:
        _validator = DataValidator()
    return _validator
