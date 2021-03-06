"""Define representation of FHIRClasses e.g. FHIR Resources."""

from .logger import logger
from typing import List, Dict, Optional, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from .fhirspec import FHIRStructureDefinitionElement, FHIRElementType

JSON_PRIMITIVE_FIELDS: Set[str] = {
    "bool",
    "float",
    "int",
    "str",
}


class FHIRClass:
    """An element/resource that should become its own class."""

    known: Dict[str, "FHIRClass"] = {}

    @classmethod
    def for_element(cls, element):
        """Return an existing class or creates one for the given element.

        Return a tuple with the class and a bool indicating creation.
        """
        assert element.represents_class
        class_name = element.name_if_class
        if class_name in cls.known:
            cls.known[class_name].add_url(element.profile.url)
            return cls.known[class_name], False

        klass = cls(element, class_name)
        cls.known[class_name] = klass
        return klass, True

    @classmethod
    def with_name(cls, class_name) -> Optional["FHIRClass"]:
        return cls.known.get(class_name)

    def __init__(self, element, class_name):
        assert element.represents_class
        self.path: str = element.path
        self.name: str = class_name
        self.module = None
        self.resource_type = element.name_of_resource()
        self.superclass = None
        self.superclass_name: str = element.superclass_name
        self.short: str = element.definition.short
        self.formal: str = element.definition.formal
        self.properties: List["FHIRClassProperty"] = []
        self.expanded_nonoptionals: Dict[str, List["FHIRClassProperty"]] = {}
        self.__urls: Set[str] = set()
        self.add_url(element.profile.url)

    def add_property(self, prop: "FHIRClassProperty") -> None:
        """Add a property to the receiver.

        :param FHIRClassProperty prop: A FHIRClassProperty instance
        """
        assert isinstance(prop, FHIRClassProperty)

        # do we already have a property with this name?
        # if we do and it's a specific reference, make it a reference to a
        # generic resource
        for existing in self.properties:
            if existing.name == prop.name:
                if len(existing.reference_to_names) == 0:
                    logger.warning(
                        f'Already have property "{prop.name}" on "{self.name}", which is only allowed for references'
                    )
                else:
                    existing.reference_to_names.extend(prop.reference_to_names)
                return

        self.properties.append(prop)

        if prop.nonoptional:
            if prop.choice_of_type is not None:
                existing_nonoptional = (
                    self.expanded_nonoptionals[prop.choice_of_type]
                    if prop.choice_of_type in self.expanded_nonoptionals
                    else []
                )
                existing_nonoptional.append(prop)
                self.expanded_nonoptionals[prop.choice_of_type] = sorted(
                    existing_nonoptional, key=lambda x: x.name
                )
            else:
                self.expanded_nonoptionals[prop.name] = [prop]

    def add_url(self, url: Optional[str]) -> None:
        if url is not None:
            self.__urls.add(url)

    @property
    def urls(self) -> List[str]:
        return list(self.__urls)

    @property
    def nonexpanded_properties(self) -> List["FHIRClassProperty"]:
        nonexpanded = []
        included = set()
        for prop in self.properties:
            if prop.choice_of_type:
                if prop.choice_of_type in included:
                    continue
                included.add(prop.choice_of_type)
            nonexpanded.append(prop)
        return nonexpanded

    @property
    def nonexpanded_properties_all(self):
        nonexpanded = self.nonexpanded_properties.copy()
        if self.superclass is not None:
            nonexpanded.extend(self.superclass.nonexpanded_properties_all)
        return nonexpanded

    @property
    def nonexpanded_nonoptionals(self):
        nonexpanded = []
        included = set()
        for prop in self.properties:
            if not prop.nonoptional:
                continue
            if prop.choice_of_type:
                if prop.choice_of_type in included:
                    continue
                included.add(prop.choice_of_type)
            nonexpanded.append(prop)
        return nonexpanded

    @property
    def nonexpanded_nonoptionals_all(self):
        nonexpanded = self.nonexpanded_nonoptionals.copy()
        if self.superclass is not None:
            nonexpanded.extend(self.superclass.nonexpanded_nonoptionals_all)
        return nonexpanded

    def property_for(self, prop_name):
        for prop in self.properties:
            if prop.orig_name == prop_name:
                return prop
        if self.superclass:
            return self.superclass.property_for(prop_name)
        return None

    def should_write(self):
        if self.superclass is not None:
            return True
        return True if len(self.properties) > 0 else False

    @property
    def has_nonoptional(self):
        for prop in self.properties:
            if prop.nonoptional:
                return True
        return False

    @property
    def has_choice_of_type(self):
        for prop in self.properties:
            if prop.choice_of_type is not None:
                return True
        return False

    @property
    def sorted_properties(self):
        return sorted(self.properties, key=lambda x: x.name)

    @property
    def sorted_properties_all(self):
        properties = self.properties.copy()
        if self.superclass is not None:
            properties.extend(self.superclass.sorted_properties_all)
        return sorted(properties, key=lambda x: x.name)

    @property
    def sorted_nonexpanded_properties(self):
        return sorted(self.nonexpanded_properties, key=lambda x: x.name)

    @property
    def sorted_nonexpanded_properties_all(self):
        return sorted(self.nonexpanded_properties_all, key=lambda x: x.name)

    @property
    def sorted_nonoptionals(self):
        return sorted(self.expanded_nonoptionals.items())

    @property
    def sorted_nonexpanded_nonoptionals(self):
        return sorted(self.nonexpanded_nonoptionals, key=lambda x: x.name)

    @property
    def sorted_nonexpanded_nonoptionals_all(self):
        return sorted(self.nonexpanded_nonoptionals_all, key=lambda x: x.name)

    @property
    def has_expanded_nonoptionals(self):
        return (
            len([p for p in self.properties if p.choice_of_type and p.nonoptional]) > 0
        )

    @property
    def has_only_expandable_properties(self):
        return len([p for p in self.properties if not p.choice_of_type]) < 1

    @property
    def resource_type_enum(self):
        return self.resource_type[:1].lower() + self.resource_type[1:]

    @property
    def choice_properties(self) -> Dict[str, list]:
        result: Dict[str, list] = {}
        for p in self.properties:
            if p.choice_of_type:
                result.setdefault(p.choice_of_type, []).append(p.name)
        return result

    @property
    def properties_map(self) -> Dict[str, "FHIRClassProperty"]:
        result: Dict[str, "FHIRClassProperty"] = {}
        for p in self.properties:
            result[p.name] = p
        return result

    def __repr__(self):
        return f"<{self.__class__.__name__}> path: {self.path}, name: {self.name}, resourceType: {self.resource_type}"


class FHIRClassProperty:
    """An element describing an instance property."""

    def __init__(
        self,
        element: "FHIRStructureDefinitionElement",
        type_obj: "FHIRElementType",
        type_name: Optional[str] = None,
    ):

        assert (
            element and type_obj
        )  # and must be instances of FHIRStructureDefinitionElement and FHIRElementType
        spec = element.profile.spec

        self.path = element.path

        # https://www.hl7.org/fhir/formats.html#choice
        # assign if this property has been expanded from "property[x]"
        self.choice_of_type: Optional[str] = None

        if not type_name:
            type_name = type_obj.code

        name = element.definition.prop_name
        if "[x]" in name:
            assert type_name is not None
            self.choice_of_type = spec.safe_property_name(name.replace("[x]", ""))
            name = name.replace("[x]", type_name[:1].upper() + type_name[1:])

        self.orig_name: str = name
        self.name: str = spec.safe_property_name(name)
        self.parent_name: str = element.parent_name
        self.class_name: str = spec.class_name_for_type_if_property(type_name)
        self.enum = element.enum if type_name == "code" else None
        self.module_name = (
            None  # should only be set if it's an external module (think Python)
        )

        # JSON class is the field type used when json encoded: dict, str, float, bool or int
        self.json_class = spec.json_class_for_class_name(self.class_name)

        # is_native means that the field type is a "native" python type
        # Note: "native" or "at least already defined in the file when generating the field"
        # Example: str, decimal.Decimal, bool, FHIRDateTime, FHIRString...
        # Exhaustive list is defined in settings > mapping_rules > natives)
        self.is_native = (
            False if self.enum else spec.class_name_is_native(self.class_name)
        )

        # A JSON primitive field is any JSON data type that is not dict (e.g "single value field")
        # /!\ `is_json_primitive_field` is different from `is_native`
        #     Example : AccountStatus is an enum, not a native type of Python but
        #               represented as a primitive JSON type (str).
        self.is_json_primitive_field = self.json_class in JSON_PRIMITIVE_FIELDS

        self.is_array = True if element.n_max == "*" else False
        self.is_summary = element.is_summary
        self.is_summary_n_min_conflict = element.summary_n_min_conflict
        self.nonoptional: bool = (
            True if element.n_min is not None and 0 != int(element.n_min) else False
        )
        self.is_optional: bool = not self.nonoptional
        self.reference_to_names: List[str] = (
            [spec.class_name_for_profile(type_obj.profile)]
            if type_obj.profile is not None
            else []
        )
        self.short = element.definition.short
        self.formal = element.definition.formal
        self.representation = element.definition.representation

    @property
    def documentation(self):
        doc = ""
        if self.enum is not None:
            doc = self.formal
            if self.enum.restricted_to is not None:
                add = f"\nRestricted to: {self.enum.restricted_to}"
                doc = doc + add if doc is not None and len(doc) > 0 else add
        else:
            doc = self.short

        if self.choice_of_type is not None:
            add = f"\nOne of `{self.choice_of_type}[x]`"
            doc = doc + add if doc is not None and len(doc) > 0 else add

        return doc

    @property
    def desired_classname(self) -> str:
        if self.enum and self.enum.is_codesystem_known:
            return self.enum.name
        elif self.enum and self.enum.restricted_to:
            return "typing.Literal"
        else:
            return self.class_name

    @property
    def nonexpanded_name(self) -> str:
        return self.choice_of_type if self.choice_of_type is not None else self.name

    @property
    def nonexpanded_classname(self) -> Optional[str]:
        if (
            self.choice_of_type is not None
        ):  # We leave it up to the template to supply a class name in this case
            return None
        return self.desired_classname

    def __repr__(self):
        return f"<FHIRClassProperty {self.name=} >"
