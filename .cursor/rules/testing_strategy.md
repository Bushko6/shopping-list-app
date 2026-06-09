# Testing Strategy — Shopping List App

## Toolchain

| Tool | Purpose |
|---|---|
| `pytest >= 8` | Test runner |
| `pytest-cov >= 5` | Branch coverage via `--cov` |
| `pytest-mock >= 3.14` | `mocker` fixture / `MagicMock` helpers |

Install: `pip install -e ".[dev]"`

---

## TDD workflow (mandatory)

1. **Red** — write a test that describes the desired behaviour. Run it; confirm it fails.
2. **Green** — write the minimum implementation to make it pass.
3. **Refactor** — clean up without breaking tests.

Never commit production code that does not have a corresponding test written first.

---

## What to test in each layer

### models/

Cover every validation branch in `__post_init__`:
- Empty or whitespace `id`, `title`, `name` → `ValueError`.
- Out-of-range numeric fields (`quantity <= 0`, `price < 0`, negative counts).
- `expires_at <= created_at` on `InviteRequest`.
- Auto-set defaults (`ShoppingList.created_at` auto-set when `None`).
- Property methods (`ShoppingList.is_archived`, `Item.is_purchased`).

### storage/ (in-memory repos)

For every repository:
- `add` stores and `get_by_id` retrieves the same object.
- `add` on a duplicate id raises `ValueError`.
- `update` on a missing id raises `KeyError`.
- `delete` on a missing id raises `KeyError`.
- `list_all` reflects current state after add/delete.
- All domain-specific query methods (`find_pending_by_list`, `total_unsettled_by_user`,
  `find_overdue`, etc.) return correct subsets.

Use `pytest.mark.parametrize` to run CRUD assertions across all seven repos with a
single parametrized test.

### services/ (unit tests with mocks)

Cover every branch in each service method:

**ListService:**
- `create_list` with and without an owner_id; unknown owner_id raises `UserNotFoundError`.
- `assign_owner` — happy path; ARCHIVED list raises `InvalidStatusTransitionError`.
- `change_status` — all valid transitions; invalid transition raises; DRAFT→ACTIVE without
  owner raises.

**ItemService:**
- `purchase` on time → `PURCHASED`, budget entry created.
- `purchase` over budget → `PURCHASED`, budget warning event fired.
- `purchase` when list not found / no list assigned → no budget entry, purchase still created.
- `purchase` on already-purchased item → `AlreadyPurchasedError`.
- `mark_skipped` → `SKIPPED`, event fired.
- Event bus `notify_list_status` called exactly once per purchase/mark-skipped.

**ShareService:**
- `invite_or_queue` with space → user added, `active_lists_count` incremented.
- `invite_or_queue` full list → `InviteRequest` created.
- `invite_or_queue` inactive user → `UserInactiveError`.
- `invite_or_queue` duplicate invite request → `DuplicateInviteRequestError`.
- `leave_list` → member removed, count decremented (floor 0), `ListSpotAvailableEvent` fired.
- `expire_old` → only requests past `expires_at` are set to `EXPIRED`.
- `get_next_in_queue` → respects priority (lower `active_lists_count` first, then FIFO).

**UserService:**
- `evaluate` → deactivates when budget entries ≥ threshold OR overdue items ≥ threshold.
- `evaluate` → reactivates when both conditions clear.
- `deactivate` / `reactivate` → force-override regardless of thresholds.
- All three methods raise `UserNotFoundError` for unknown user.

**SortingStrategy:**
- Each strategy: empty list → empty result.
- Each strategy: non-empty list → correct order.
- `CategorySortStrategy`: items grouped by category.
- `StatusSortStrategy`: PENDING before PURCHASED before SKIPPED.
- `PriceSortStrategy`: ascending price order, ties broken by name.
- `SortingStrategyFactory.from_name`: known names return correct type; unknown raises.

**Observer / EventBus:**
- Subscribe is idempotent (second subscribe of same observer has no effect).
- Unsubscribe of unregistered observer raises `ValueError`.
- Notify dispatches to a snapshot — observer may unsubscribe mid-dispatch without error.
- `UserNotifier.on_list_status_changed` records notification for each list member.
- `UserNotifier.on_list_spot_available` records notification for highest-priority
  queued user only.

### integration/

Wire real repos + services (no mocks). Cover the three end-to-end scenarios:

1. **Over-budget purchase → budget entry → settle → reactivate**
   - List created, user assigned, item purchased over budget.
   - Budget entries stored; `evaluate()` deactivates user.
   - Entries settled; `evaluate()` reactivates user.

2. **Full list → priority queue → leave → notify**
   - Two users with different `active_lists_count` queue for a full list.
   - A member leaves; the user with fewer active lists is notified, not the
     one who queued first.

3. **Overdue items → deactivated → invite rejected → reactivated → invite succeeds**
   - User accumulates `overdue_items_count` via skipped items.
   - `evaluate()` deactivates; `invite_or_queue` raises `UserInactiveError`.
   - `reactivate()` called; `invite_or_queue` succeeds.

---

## Parametrize for breadth

```python
@pytest.mark.parametrize("items,expected_order", [
    ([], []),
    (["Milk", "Apples", "Bread"], ["Apples", "Bread", "Milk"]),
])
def test_alphabetic_sort_strategy_various_inputs(items, expected_order):
    strategy = AlphabeticSortStrategy()
    result = strategy.sort([Item(name=n) for n in items])
    assert [i.name for i in result] == expected_order
```

Use parametrize wherever a method has a clear input→output table (strategy formulas,
validation edge cases, status transitions).

---

## Clock injection pattern

Never call `datetime.now()` directly in tests. All services accept an injectable clock:

```python
# Freeze time at creation date (on-time purchase)
svc = ItemService(..., clock=lambda: added)

# Advance time (late purchase)
svc = ItemService(..., clock=lambda: added + timedelta(days=3))
```

For integration tests, use the advanceable `Clock` helper from `tests/integration/conftest.py`:

```python
clock.set(added + timedelta(days=5))   # jump to specific instant
clock.advance(days=2)                  # relative advance
```

---

## Coverage target

**Branch coverage >= 85%.** Every `if` / `else` / `elif`, every `or` / `and` short-circuit,
and every loop body must be exercised by at least one test.

Run `pytest --cov=src --cov-branch --cov-report=term-missing` and inspect the
`Missing` column. Add targeted tests for any uncovered branch before merging.

---

## What NOT to test

- `__init__.py` files (excluded from coverage via `pyproject.toml`).
- Third-party library internals.
- Pure data containers where the only logic is Python's own dataclass machinery.
