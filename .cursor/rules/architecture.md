# Architecture — In-Memory Shopping List App

## Layer overview

```
models  →  storage  →  services  →  (CLI / tests)
```

Each layer depends only on the layer to its left via abstractions, never on concrete implementations.

---

## models/

**Responsibility:** pure data — no business logic, no I/O.

Contains dataclass entities:
- `User` — id, name, email, is_active, active_lists_count, overdue_items_count
- `ShoppingList` — id, title, owner_id, status (DRAFT/ACTIVE/COMPLETED/ARCHIVED), created_at
- `Item` — id, list_id, name, quantity, unit, category_id, status (PENDING/PURCHASED/SKIPPED), price, added_at
- `Category` — id, name, color
- `Purchase` — id, item_id, list_id, purchased_by, purchased_at, actual_price
- `BudgetEntry` — id, user_id, list_id, amount, is_settled
- `InviteRequest` — id, user_id, list_id, created_at, expires_at, status (PENDING/FULFILLED/EXPIRED/CANCELLED)

Rules:
- All fields are typed.
- Validation (e.g. negative quantities, empty id) raises `ValueError` in `__post_init__`, not a service exception.
- No imports from `storage` or `services`.

---

## storage/

**Responsibility:** data persistence — currently all in-memory via plain Python dicts.

### Sub-structure

```
storage/
  interfaces.py                  # abc.ABC repository contracts
  memory/
    user_repo.py
    shopping_list_repo.py
    item_repo.py
    category_repo.py
    purchase_repo.py
    budget_entry_repo.py
    invite_request_repo.py
```

### Repository interfaces (interfaces.py)

Every repository is an `abc.ABC` with `@abstractmethod` operations:

```python
class UserRepository(ABC):
    @abstractmethod
    def add(self, user: User) -> None: ...
    @abstractmethod
    def get_by_id(self, user_id: str) -> User | None: ...
    @abstractmethod
    def list_all(self) -> list[User]: ...
    @abstractmethod
    def update(self, user: User) -> None: ...
    @abstractmethod
    def delete(self, user_id: str) -> None: ...
```

The same CRUD pattern applies to all seven repositories. Specialised query methods
(e.g. `find_pending_by_list`, `total_unsettled_by_user`, `find_overdue`) are
declared on the relevant ABCs only — Interface Segregation in practice.

### In-memory implementations

Concrete classes (e.g. `InMemoryUserRepository(UserRepository)`) store data in
`dict[str, User]`. They import only from `models/`; they have no knowledge of services.

**Why ABCs decouple services from storage:**
Services receive a `UserRepository` (the ABC) via constructor injection. The service
never calls `InMemoryUserRepository()` directly. This means:
- The in-memory impl can be swapped for a SQL impl without touching services.
- Unit tests inject a `MagicMock` that satisfies the ABC interface.

---

## services/

**Responsibility:** all business logic — list lifecycle, item purchases, share
management, budget tracking, and user deactivation.

### Key services

| Service | Depends on |
|---|---|
| `ListService` | `ShoppingListRepository`, `UserRepository` |
| `ItemService` | `ItemRepository`, `PurchaseRepository`, `BudgetEntryRepository`, `ShoppingListRepository`, `CategoryRepository`, `UserRepository`, `SortingStrategy`, `ListSubject` |
| `ShareService` | `ShoppingListRepository`, `UserRepository`, `InviteRequestRepository`, `ListSubject` |
| `UserService` | `UserRepository`, `BudgetEntryRepository` |

### Dependency Injection

All dependencies are injected through `__init__`:

```python
class ItemService:
    def __init__(
        self,
        item_repo: ItemRepository,
        purchase_repo: PurchaseRepository,
        budget_entry_repo: BudgetEntryRepository,
        list_repo: ShoppingListRepository,
        category_repo: CategoryRepository,
        user_repo: UserRepository,
        sorting_strategy: SortingStrategy,
        event_bus: ListSubject,
        clock: Callable[[], datetime] = datetime.now,
    ) -> None:
        ...
```

A composition root (e.g. the integration-test `conftest.py`) wires concrete
implementations together and is the only place that calls `InMemory*` constructors.

---

## utils/

**Responsibility:** cross-cutting concerns that belong to no single layer.

- `exceptions.py` — domain exception hierarchy (`UserNotFoundError`, `ListFullError`,
  `InvalidStatusTransitionError`, `AlreadyPurchasedError`, `DuplicateInviteRequestError`, …).

`utils/` imports nothing from `services/` or `storage/`.

---

## GoF Pattern locations

### Strategy — item sorting

```
services/sorting_strategies.py  → SortingStrategy(ABC)
                                → AlphabeticSortStrategy
                                → CategorySortStrategy
                                → StatusSortStrategy
                                → PriceSortStrategy  (Decorator)
                                → SortingStrategyFactory
```

`ItemService` receives a `SortingStrategy` and calls
`strategy.sort(items)`. Switching the sort policy requires
only a different strategy object at the composition root, not a code change.

### Observer — list status and share-spot notifications

```
services/events.py        → ListSubject(ABC), ListObserver(ABC)
                          → EventBus (implements ListSubject)
                          → ListStatusChangedEvent, ListSpotAvailableEvent
services/notification.py  → UserNotifier (implements ListObserver)
```

`ListService` publishes `ListStatusChangedEvent` after every status change.
`ShareService` publishes `ListSpotAvailableEvent` after a user leaves a shared list.
`UserNotifier` reacts by recording `Notification` objects — services have no knowledge
of what happens next (Open/Closed in action).

---

## Dependency direction summary

```
services  →  storage interfaces (ABC)  ←  storage implementations
services  →  models
services  →  utils (exceptions, events, sorting_strategies)
storage   →  models
utils     →  (nothing in src)
```

No circular imports. `models` is imported by every layer; it imports nothing.
