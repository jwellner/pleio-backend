from dataclasses import dataclass

@dataclass
class PaginateResult:
    total: int # The total amount of items (without limits and offsets)
    edges: list # The list of items that are to be returned for this request
