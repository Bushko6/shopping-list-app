# Architecture Reference — Shopping List App

## Entities (`src/models/`)

| Class | Key fields |
|---|---|
| `User` | id, name, email, is_active, active_lists_count, overdue_items_count |
| `ShoppingList` | id, title, owner_id, status (DRAFT/ACTIVE/COMPLETED/ARCHIVED), created_at |
| `Item` | id, list_id, name, quantity, unit, category_id, status (PENDING/PURCHASED/SKIPPED), price, added_at |
| `Category` | id, name, color |
| `Purchase` | id, item_id, list_id, purchased_by, purchased_at, actual_price |
| `BudgetEntry` | id, user_id, list_id, amount, is_settled |
| `InviteRequest` | id, user_id, list_id, created_at, expires_at, status (PENDING/FULFILLED/EXPIRED/CANCELLED) |

## Repository ABCs (`src/storage/interfaces.py`)

One ABC per entity: `UserRepository`, `ShoppingListRepository`, `ItemRepository`,
`CategoryRepository`, `PurchaseRepository`, `BudgetEntryRepository`, `InviteRequestRepository`.

Specialised query methods beyond basic CRUD:
- `ItemRepository.find_overdue(as_of)` — PENDING items past `added_at` threshold
- `BudgetEntryRepository.total_unsettled_by_user(user_id) -> int`
- `InviteRequestRepository.find_pending_by_list(list_id)`

## Services (`src/services/`)

| Service | Responsibility | Key injected deps |
|---|---|---|
| `ListService` | Shopping list lifecycle (create, assign owner, change status) | `ShoppingListRepository`, `UserRepository` |
| `ItemService` | Purchases, skipped marks, budget entry creation, event firing | All repos + `SortingStrategy` + `ListSubject` |
| `ShareService` | Invite/queue/leave, queue expiry, priority ordering | `ShoppingListRepository`, `UserRepository`, `InviteRequestRepository`, `ListSubject` |
| `UserService` | Evaluate/deactivate/reactivate based on budget entries and overdue items | `UserRepository`, `BudgetEntryRepository` |

## GoF patterns

### Strategy — item sorting

`SortingStrategy` (ABC) in `src/services/sorting_strategies.py`.  
Concrete strategies: `AlphabeticSortStrategy`, `CategorySortStrategy`,
`StatusSortStrategy`, `PriceSortStrategy` (Decorator).  
Factory: `SortingStrategyFactory`.  
Injected into `ItemService`; called as `strategy.sort(items) -> list[Item]`.

### Observer — list status + share-spot events

ABCs: `ListSubject`, `ListObserver` — both in `src/services/events.py`.  
Concrete subject: `EventBus` (snapshot-based dispatch, idempotent subscribe).  
Events: `ListStatusChangedEvent`, `ListSpotAvailableEvent`.  
Concrete observer: `UserNotifier` (`src/services/notification.py`) — records
`Notification` objects for list members (on status change) and the top-priority
queued user (on share-spot event).

## Valid list status transitions

```
DRAFT  →  ACTIVE (requires owner_id set)
DRAFT  →  ARCHIVED
ACTIVE →  COMPLETED
ACTIVE →  ARCHIVED
COMPLETED → ARCHIVED
ARCHIVED  → (terminal)
```

## Invite queue priority key

`(user.active_lists_count, invite_request.created_at)` — ascending.  
Lower active-list count wins; FIFO within the same count.
