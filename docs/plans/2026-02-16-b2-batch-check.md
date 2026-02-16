# b2 --check: Batch IP Check Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a `--check` flag to `b2` that iterates over all bound ports after a batch bind and runs IP fetch + DNS leak test for each, skipping failures gracefully.

**Architecture:** `--check` is a modifier flag (like `--debug`/`--wait`) parsed in phase 1 of `b2()`. After `_b2_gen_and_bind()` completes, if `--check` is set, a new `_b2_batch_check()` helper loops over the bound ports and calls `c3` for each. Ports where `c3` fails are skipped with a warning. The bound ports are communicated from `_b2_gen_and_bind()` to `b2()` via a namespaced global `_B2_BOUND_PORTS`.

**Tech Stack:** Zsh (core.sh only), no Python changes, no proxy_converter changes.

---

### Task 1: Expose bound_ports from _b2_gen_and_bind()

**Files:**
- Modify: `mrtamaki-1.7.0/core.sh:414-525` (`_b2_gen_and_bind`)

**Step 1: Add global port export at the end of _b2_gen_and_bind()**

Before the cleanup trap (line 513), after the summary block, add:

```zsh
    # Export bound ports for --check flag
    typeset -ga _B2_BOUND_PORTS=("${bound_ports[@]}")
```

Insert this right after line 506 (`echo ""`), before line 508 (`if [[ ${#bg_pids[@]} -eq 0 ]]`).

**Step 2: Verify manually**

Run: `grep -n '_B2_BOUND_PORTS' mrtamaki-1.7.0/core.sh`
Expected: One line showing the typeset assignment.

---

### Task 2: Refactor b2() dispatch to not early-return after batch gen

**Files:**
- Modify: `mrtamaki-1.7.0/core.sh:650-658` (`b2` dispatch section)

**Step 1: Change early returns to capture exit code**

Currently lines 652-658 do `return $?` immediately after `_b2_gen_and_bind`. Change to capture exit code and fall through:

```zsh
    if [[ "$flag" == "gen_a1" ]]; then
        _b2_gen_and_bind "a1" "$gen_count" "$gen_city" "$project_path" "$debug_flag"
        exit_code=$?

    elif [[ "$flag" == "gen_a2" ]]; then
        _b2_gen_and_bind "a2" "$gen_count" "$gen_city" "$project_path" "$debug_flag"
        exit_code=$?

    elif [[ "$flag" == "bind" ]]; then
```

This allows execution to continue past the dispatch block into the --check logic (Task 4).

---

### Task 3: Add --check flag parsing to b2()

**Files:**
- Modify: `mrtamaki-1.7.0/core.sh:542-607` (`b2` flag parsing)

**Step 1: Add do_check variable initialization**

After line 549 (`local gen_city=""`), add:

```zsh
    local do_check=false
```

**Step 2: Add --check case to the while loop**

In the case block (between the `--wait` case at line 594-596 and the `--help` case at line 597), add:

```zsh
            --check|-k)
                do_check=true
                ;;
```

---

### Task 4: Add _b2_batch_check() helper and invoke it after dispatch

**Files:**
- Modify: `mrtamaki-1.7.0/core.sh` (insert before `b2()` function, after `_b2_gen_and_bind()`)

**Step 1: Write the batch check helper function**

Insert after line 525 (end of `_b2_gen_and_bind`), before line 527 (`b2()`):

```zsh
# ── Helper: batch check IPs after bind ──────────────────────────────────
# Iterates over _B2_BOUND_PORTS, runs c3 (IP fetch + DNS leak) for each.
# Skips ports where the proxy is unreachable.

_b2_batch_check() {
    local -a ports=("${_B2_BOUND_PORTS[@]}")
    local total=${#ports[@]}

    if [[ $total -eq 0 ]]; then
        print_warning "No bound ports to check"
        return 1
    fi

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🔍 Batch IP Check — $total port(s)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    local idx=0
    local passed=0
    local failed=0

    for port_val in "${ports[@]}"; do
        idx=$((idx + 1))
        print_header "[$idx/$total] Checking port $port_val"

        if c3 "$port_val"; then
            passed=$((passed + 1))
        else
            failed=$((failed + 1))
            print_warning "[$idx/$total] Port $port_val — check failed, skipping"
        fi

        # Separator between checks (skip after last)
        if [[ $idx -lt $total ]]; then
            echo ""
            echo "───────────────────────────────────────────────────"
            echo ""
        fi
    done

    # ── Summary ───────────────────────────────────────────────────────
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🔍 Batch Check Complete — $passed passed, $failed failed"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
}
```

**Step 2: Add the --check invocation in b2() after the dispatch block**

After the dispatch block (after the gen_a1/gen_a2/bind/list/else cases close, around line 682), before the exit code check at line 684, insert:

```zsh
    # ── Batch check (--check flag) ─────────────────────────────────────
    if $do_check; then
        if [[ ${#_B2_BOUND_PORTS[@]} -gt 0 ]]; then
            _b2_batch_check
        else
            print_warning "No ports were bound — skipping --check"
        fi
        unset _B2_BOUND_PORTS
    fi
```

---

### Task 5: Update help text

**Files:**
- Modify: `mrtamaki-1.7.0/core.sh:609-633` (`b2` help section)

**Step 1: Add --check to the flags list**

After the `--wait` line (line 622), add:

```zsh
        printf "  %-28s %s\n" "--check, -k" "Check IPs + DNS leak after batch bind"
```

**Step 2: Add --check examples**

After the debug example line (line 632), add:

```zsh
        printf "  b2 --a1 3 --check               # 3 IPRoyal + check all IPs\n"
        printf "  b2 --a2 2 auckland --check       # 2 Oxylabs Auckland + check\n"
```

---

### Task 6: Commit

```bash
git add mrtamaki-1.7.0/core.sh
git commit -m "feat(b2): add --check flag for batch IP check after bind"
```
