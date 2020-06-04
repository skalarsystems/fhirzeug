import pydantic

FHIRDateTime = pydantic.constr(
    regex="([0-9]([0-9]([0-9][1-9]|[1-9]0)|[1-9]00)|[1-9]000)(-(0[1-9]|1[0-2])(-(0[1-9]|[1-2][0-9]|3[0-1])(T([01][0-9]|2[0-3]):[0-5][0-9]:([0-5][0-9]|60)(\.[0-9]+)?(Z|(\+|-)((0[0-9]|1[0-3]):[0-5][0-9]|14:00)))?)?)?"
)
FHIRDate = pydantic.constr(
    regex="([0-9]([0-9]([0-9][1-9]|[1-9]0)|[1-9]00)|[1-9]000)(-(0[1-9]|1[0-2])(-(0[1-9]|[1-2][0-9]|3[0-1]))?)?"
)
FHIRInstant = pydantic.constr(
    regex="([0-9]([0-9]([0-9][1-9]|[1-9]0)|[1-9]00)|[1-9]000)-(0[1-9]|1[0-2])-(0[1-9]|[1-2][0-9]|3[0-1])T([01][0-9]|2[0-3]):[0-5][0-9]:([0-5][0-9]|60)(\.[0-9]+)?(Z|(\+|-)((0[0-9]|1[0-3]):[0-5][0-9]|14:00))"
)
FHIRTime = pydantic.constr(
    regex="([01][0-9]|2[0-3]):[0-5][0-9]:([0-5][0-9]|60)(\.[0-9]+)?"
)
FHIRCode = pydantic.constr(regex="[^\s]+(\s[^\s]+)*")

FHIROid = pydantic.constr(regex="urn:oid:[0-2](\.(0|[1-9][0-9]*))+")

FHIRId = pydantic.constr(regex="[A-Za-z0-9\-\.]{1,64}")

FHIRBase64Binary = pydantic.constr(regex="(\s*([0-9a-zA-Z\+\=]){4}\s*)+")
