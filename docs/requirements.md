# Requirements

## Problem Statement

A user needs a **shopping list application** that lets them create and manage named lists of grocery items, sort items by multiple criteria, persist lists across sessions, and receive an automatic notification when every item on a list has been purchased.

Three design challenges drive the architecture:

| Challenge | Solution |
|---|---|
| **Sorting algorithms** must be swappable at runtime without modifying existing code. | Strategy Pattern — `SortStrategy` ABC with five concrete implementations, selected via `SortStrategyFactory`. |
| **JSON persistence** must be optional and interchangeable with in-memory storage. | Repository Pattern — `ShoppingListRepository` / `ShoppingItemRepository` ABCs with separate `InMemory*` and `JsonFile*` implementations. |
| **Completion notification** must fire automatically when all items are purchased, decoupled from the purchase logic. | Observer Pattern — `ShoppingListSubject` notifies registered `ItemObserver` instances; `ListCompletionObserver` writes to `NotificationLog`. |

---

## Actors

| Actor | Description |
|---|---|
| **User** | A person interacting with the system to manage shopping lists and items. |
| **System** | The application itself — reacts to internal domain events (e.g., all items purchased) without direct user interaction. |

---

## Use Cases

### UC1 — Create Shopping List

**Actor:** User  
**Goal:** Create a new, active shopping list with a given name.

**Main Flow:**
1. User provides `id`, `name`, and `owner_id`.
2. System validates fields (non-empty id/name/owner_id).
3. System creates `ShoppingList` with `status = ACTIVE` and `created_at = now()`.
4. System stores the list via `ShoppingListRepository.add`.
5. System returns the created `ShoppingList`.

**Alternative Flows:**
- A1: `name` is empty or blank → `ValueError("name cannot be empty")`. List not created.
- A2: `owner_id` is empty or blank → `ValueError("owner_id cannot be empty")`. List not created.

---

### UC2 — Add Item to List

**Actor:** User  
**Goal:** Add a product with quantity (and optional attributes) to an active list.

**Preconditions:** The target list exists and is `ACTIVE`.

**Main Flow:**
1. User provides `list_id`, `item_id`, `name`, `quantity`, and optional `unit`, `category`, `price`.
2. System validates the list exists and is active.
3. System validates item fields (non-empty name, positive quantity, non-negative price).
4. System creates `ShoppingItem` and stores it.
5. System fires `ITEM_ADDED` event.
6. System calls `_check_completion`; if all items are purchased it fires `LIST_COMPLETED`.
7. System returns the created `ShoppingItem`.

**Alternative Flows:**
- A1: List not found → `ShoppingListNotFoundError`.
- A2: List is `ARCHIVED` → `ListArchivedError`.
- A3: Invalid item fields → `ValueError`.

---

### UC3 — Mark Item as Purchased

**Actor:** User  
**Goal:** Record that an item has been bought.

**Preconditions:** The item exists and is not yet purchased.

**Main Flow:**
1. User provides `item_id`.
2. System retrieves the item from the repository.
3. System sets `is_purchased = True` and `purchased_at = now()`.
4. System saves the updated item.
5. System returns the updated `ShoppingItem`.

**Alternative Flows:**
- A1: Item not found → `ShoppingItemNotFoundError`.
- A2: Item already purchased → `ItemAlreadyPurchasedError`.

**Extension (UC6):** After marking purchased, if all items on the list are now purchased, `LIST_COMPLETED` is fired (triggered by the next `add_item` or `remove_item` that calls `_check_completion`).

---

### UC4 — Sort Items

**Actor:** User  
**Goal:** Retrieve items in a requested order without mutating stored data.

**Main Flow:**
1. User requests items for a `list_id` with a chosen sort order.
2. System selects the corresponding `SortStrategy` (via `SortStrategyFactory.from_name` or direct injection).
3. System calls `strategy.sort(items)` on the items retrieved from the repository.
4. System returns the sorted list. Original storage order is unchanged.

**Sort Strategies:**

| Name | Ordering |
|---|---|
| `alphabetical` | Item name ascending (case-insensitive) |
| `category` | Category name ascending; items without category last; then name ascending within group |
| `price_asc` | Price ascending; ties broken by name ascending |
| `price_desc` | Price descending; ties broken by name ascending |
| `unpurchased_first` | Unpurchased items first; within each group, name ascending |

**Alternative Flows:**
- A1: Unknown strategy name passed to `SortStrategyFactory.from_name` → `ValueError("Unknown sort strategy: '…'")`.

---

### UC5 — Save / Load List

**Actor:** User  
**Goal:** Persist the current state of lists and items to a JSON file; reload it in a new session.

**Main Flow (Save):**
1. User (or `ShoppingListService`) calls `PersistenceService.save_list` / `save_item`.
2. `PersistenceService` checks if the entity already exists in the repository.
3. If new → `repository.add`; if existing → `repository.update`.
4. `JsonFileShoppingListRepository` / `JsonFileShoppingItemRepository` serialises all records to the JSON file.

**Main Flow (Load):**
1. User instantiates a `JsonFile*Repository` pointing to an existing file.
2. Repository deserialises the JSON into domain objects on `__init__`.
3. User calls `PersistenceService.load_list` / `load_item` by ID.
4. Service returns the object, or `None` if not found.

**Alternative Flows:**
- A1: File does not exist → repository starts with an empty store; no error.
- A2: File contains invalid JSON → `json.JSONDecodeError` raised at repository construction time.
- A3: ID not found → `load_list` / `load_item` returns `None`.

---

### UC6 — Receive Completion Notification

**Actor:** System  
**Trigger:** All items on a non-empty list are purchased.

**Main Flow:**
1. `ShoppingListService._check_completion(list_id)` is called after any `add_item` or `remove_item`.
2. System queries all items for the list.
3. If the list is non-empty and every item has `is_purchased = True`, System fires `LIST_COMPLETED` via `ShoppingListSubject.notify`.
4. `ListCompletionObserver.on_event` receives the event and writes `"List '{list_id}' is complete!"` to `NotificationLog`.
5. User retrieves the message via `NotificationService.get_notifications(list_id)`.

**Alternative Flows:**
- A1: List is empty after the operation → `_check_completion` returns without firing `LIST_COMPLETED`.
- A2: One or more items are unpurchased → `LIST_COMPLETED` is not fired.
- A3: No observers subscribed to `ShoppingListSubject` → `notify` iterates an empty list; no side effects.
