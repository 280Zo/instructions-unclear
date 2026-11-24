#!/usr/bin/env python3
"""
bnhl.py - Binary Ninja HEADLESS CLI.

Decompile / analyze arbitrary binaries without loading them into the BN GUI.
Requires a licensed Binary Ninja (Commercial/Enterprise/Ultimate). A license
that validates locally needs no enterprise-server checkout and runs fine
alongside a running GUI instance.

The BN python API is usually NOT on the default sys.path; this script locates
and inserts it, so you can run the script with a plain `python3` and no
PYTHONPATH juggling. Set $BN_PYTHON to your install's `python` dir to override
the autodetected locations below.

Analysis is cached to a .bndb under a cache dir keyed by (path, mtime, size),
so the first call on a big binary pays the analysis cost once and every later
call is instant.

Usage (run with plain python3):
  bnhl.py info      <bin>
  bnhl.py functions <bin> [--filter REGEX] [--limit N]
  bnhl.py decompile <bin> <func|0xADDR> [<func2> ...] [--il pseudoc|hlil|mlil|disasm]
  bnhl.py xrefs     <bin> <func|0xADDR>          # who calls / references this
  bnhl.py callees   <bin> <func|0xADDR>          # what this calls
  bnhl.py strings   <bin> [--filter REGEX] [--min N]
  bnhl.py grepstr   <bin> <REGEX>                # strings + the functions that reference them
  bnhl.py imports   <bin>
  bnhl.py exports   <bin>
  bnhl.py sections  <bin>
  bnhl.py at        <bin> <0xADDR>               # which function contains an address, decompiled

func selector: exact symbol name, unique substring, or a hex address (0x...).
Add --raw to any command for machine-readable JSON where supported.
"""
import sys, os, re, json, hashlib, argparse

# ---- locate + inject the BN python API ---------------------------------------
# $BN_PYTHON (or $BN_INSTALL_DIR/python) wins; otherwise try common locations.
BN_PYTHON_CANDIDATES = [
    os.environ.get("BN_PYTHON", ""),
    os.path.join(os.environ.get("BN_INSTALL_DIR", ""), "python") if os.environ.get("BN_INSTALL_DIR") else "",
    os.path.expanduser("~/binaryninja/python"),
    "/opt/binaryninja/python",
    "/Applications/Binary Ninja.app/Contents/Resources/python",
]
for p in BN_PYTHON_CANDIDATES:
    if p and os.path.isdir(os.path.join(p, "binaryninja")):
        sys.path.insert(0, p)
        break
try:
    import binaryninja as bn
    from binaryninja import DisassemblySettings, LinearViewObject, LinearViewCursor
    from binaryninja.enums import DisassemblyOption
except Exception as e:
    print(f"[!] cannot import binaryninja API: {e}", file=sys.stderr)
    print("[!] set $BN_PYTHON to your Binary Ninja install's 'python' directory", file=sys.stderr)
    sys.exit(3)

bn.disable_default_log()  # keep stdout clean for parsing

CACHE_DIR = os.environ.get("BNHL_CACHE", os.path.expanduser("~/.cache/bnhl"))
os.makedirs(CACHE_DIR, exist_ok=True)


def _cache_key(path):
    st = os.stat(path)
    h = hashlib.sha1(f"{os.path.abspath(path)}:{st.st_mtime_ns}:{st.st_size}".encode()).hexdigest()[:16]
    base = re.sub(r"[^A-Za-z0-9_.-]", "_", os.path.basename(path))
    return os.path.join(CACHE_DIR, f"{base}.{h}.bndb")


def load_bv(path, update=True):
    if not os.path.exists(path):
        print(f"[!] no such file: {path}", file=sys.stderr); sys.exit(2)
    bndb = _cache_key(path)
    if os.path.exists(bndb):
        bv = bn.load(bndb)
        if bv is not None:
            bv.update_analysis_and_wait()
            return bv
    bv = bn.load(path, update_analysis=update)
    if bv is None:
        print(f"[!] BN failed to load {path}", file=sys.stderr); sys.exit(2)
    bv.update_analysis_and_wait()
    try:
        bv.create_database(bndb)
    except Exception:
        pass
    return bv


def resolve_funcs(bv, sel):
    """sel -> list of functions. hex addr, exact name, or substring."""
    if isinstance(sel, str) and re.fullmatch(r"0x[0-9a-fA-F]+", sel):
        addr = int(sel, 16)
        f = bv.get_function_at(addr)
        if f:
            return [f]
        fns = bv.get_functions_containing(addr) or []
        return list(fns)
    exact = [f for f in bv.functions if f.name == sel]
    if exact:
        return exact
    sub = [f for f in bv.functions if sel in f.name]
    return sub


# ---- pseudo-C for a single function ------------------------------------------
def func_pseudoc(bv, f):
    settings = DisassemblySettings()
    try:
        settings.set_option(DisassemblyOption.ShowAddress, False)
    except Exception:
        pass
    ranges = list(f.address_ranges)
    lo = min(r.start for r in ranges); hi = max(r.end for r in ranges)
    for attempt in range(6):
        obj = LinearViewObject.language_representation(bv, settings)
        cur = LinearViewCursor(obj)
        cur.seek_to_address(f.start)
        body, guard, seen_body, loading = [], 0, False, False
        while True:
            guard += 1
            if guard > 20000:
                break
            lines = cur.lines
            if lines:
                past = False
                for l in lines:
                    addr = getattr(getattr(l, "contents", None), "address", None)
                    txt = str(l)
                    if "Loading..." in txt:
                        loading = True
                        break
                    if addr is not None and lo <= addr < hi:
                        seen_body = True
                    if addr is not None and seen_body and addr >= hi:
                        past = True
                        break
                    body.append(txt)
                if past or loading:
                    break
            if not cur.next():
                break
        if not loading:
            return "\n".join(body).rstrip()
        # linear view not settled (typical after a bndb cache-restore); a one-time
        # reanalyze materializes the pseudo-C language representation.
        if not getattr(bv, "_bnhl_reanalyzed", False):
            bv.reanalyze()
            bv._bnhl_reanalyzed = True
        bv.update_analysis_and_wait()
    return "\n".join(body).rstrip()


def func_il(bv, f, il):
    lines = []
    if il == "hlil":
        try:
            for line in f.hlil.root.lines:
                lines.append(str(line))
        except Exception:
            for bb in f.hlil:
                for ins in bb:
                    lines.append(str(ins))
    elif il == "mlil":
        for bb in f.mlil:
            for ins in bb:
                lines.append(f"{ins.address:#x}  {ins}")
    elif il == "disasm":
        for bb in f:
            for line in bb.get_disassembly_text():
                lines.append(f"{line.address:#x}  {line}")
    return "\n".join(lines)


# ---- commands ----------------------------------------------------------------
def cmd_info(bv, a):
    print(f"path        : {bv.file.filename}")
    print(f"arch        : {bv.arch}")
    print(f"platform    : {bv.platform}")
    print(f"entry       : {bv.entry_point:#x}")
    print(f"functions   : {len(list(bv.functions))}")
    print(f"strings     : {len(list(bv.strings))}")
    print(f"imports     : {len(list(bv.get_symbols_of_type(bn.SymbolType.ImportedFunctionSymbol)))}")
    print("sections    :")
    for name, s in bv.sections.items():
        print(f"  {name:20s} {s.start:#010x}-{s.end:#010x}  ({s.end-s.start} bytes)")


def cmd_functions(bv, a):
    rx = re.compile(a.filter) if a.filter else None
    rows = []
    for f in bv.functions:
        if rx and not rx.search(f.name):
            continue
        rows.append((f.start, f.total_bytes, f.name))
    rows.sort()
    if a.limit:
        rows = rows[: a.limit]
    if a.raw:
        print(json.dumps([{"addr": hex(s), "size": sz, "name": n} for s, sz, n in rows], indent=2))
        return
    for s, sz, n in rows:
        print(f"{s:#010x}  {sz:6d}  {n}")
    print(f"\n[{len(rows)} functions]", file=sys.stderr)


def cmd_decompile(bv, a):
    for sel in a.func:
        fns = resolve_funcs(bv, sel)
        if not fns:
            print(f"[!] no function matching {sel!r}", file=sys.stderr); continue
        if len(fns) > 8:
            print(f"[!] {sel!r} matches {len(fns)} functions; showing first 8 (use exact name/addr)", file=sys.stderr)
            fns = fns[:8]
        for f in fns:
            print(f"\n// ===== {f.name} @ {f.start:#x}  ({f.total_bytes} bytes)  =====")
            if a.il == "pseudoc":
                print(func_pseudoc(bv, f))
            else:
                print(func_il(bv, f, a.il))


def cmd_xrefs(bv, a):
    fns = resolve_funcs(bv, a.func)
    if not fns:
        print(f"[!] no function matching {a.func!r}", file=sys.stderr); sys.exit(2)
    f = fns[0]
    print(f"// xrefs TO {f.name} @ {f.start:#x}")
    callers = list(f.callers)
    for c in callers:
        print(f"  caller  {c.start:#010x}  {c.name}")
    seen = set(c.start for c in callers)
    for ref in bv.get_code_refs(f.start):
        cf = ref.function
        if cf and cf.start not in seen:
            print(f"  coderef {ref.address:#010x}  in {cf.name}")
            seen.add(cf.start)
    if not seen:
        print("  (none)")


def cmd_callees(bv, a):
    fns = resolve_funcs(bv, a.func)
    if not fns:
        print(f"[!] no function matching {a.func!r}", file=sys.stderr); sys.exit(2)
    f = fns[0]
    print(f"// callees OF {f.name} @ {f.start:#x}")
    for c in sorted(set(f.callees), key=lambda x: x.start):
        print(f"  {c.start:#010x}  {c.name}")


def cmd_strings(bv, a):
    rx = re.compile(a.filter) if a.filter else None
    for s in bv.strings:
        if len(s.value) < a.min:
            continue
        if rx and not rx.search(s.value):
            continue
        print(f"{s.start:#010x}  {s.value!r}")


def cmd_grepstr(bv, a):
    rx = re.compile(a.regex)
    hits = 0
    for s in bv.strings:
        if not rx.search(s.value):
            continue
        hits += 1
        print(f"\n{s.start:#010x}  {s.value!r}")
        refd = set()
        for ref in bv.get_code_refs(s.start):
            cf = ref.function
            if cf and cf.start not in refd:
                print(f"    <- {ref.address:#010x}  {cf.name}")
                refd.add(cf.start)
        if not refd:
            print("    <- (no direct code refs)")
    print(f"\n[{hits} matching strings]", file=sys.stderr)


def cmd_imports(bv, a):
    for sym in bv.get_symbols_of_type(bn.SymbolType.ImportedFunctionSymbol):
        print(f"{sym.address:#010x}  {sym.name}")


def cmd_exports(bv, a):
    for sym in bv.get_symbols_of_type(bn.SymbolType.FunctionSymbol):
        if sym.binding in (bn.SymbolBinding.GlobalBinding, bn.SymbolBinding.WeakBinding):
            print(f"{sym.address:#010x}  {sym.name}")


def cmd_sections(bv, a):
    for name, s in bv.sections.items():
        print(f"{name:24s} {s.start:#010x}-{s.end:#010x}  {s.semantics}")


def cmd_at(bv, a):
    addr = int(a.addr, 16)
    fns = bv.get_functions_containing(addr) or []
    if not fns:
        print(f"[!] no function contains {addr:#x}", file=sys.stderr); sys.exit(2)
    for f in fns:
        print(f"\n// ===== {f.name} @ {f.start:#x} (contains {addr:#x}) =====")
        print(func_pseudoc(bv, f))


def main():
    ap = argparse.ArgumentParser(prog="bnhl", description="Binary Ninja headless CLI")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def add(name, fn, addfunc=False, extra=None):
        p = sub.add_parser(name)
        p.add_argument("bin")
        if addfunc:
            p.add_argument("func", nargs="+" if name == "decompile" else 1)
        p.add_argument("--raw", action="store_true")
        if extra:
            extra(p)
        p.set_defaults(_fn=fn)
        return p

    add("info", cmd_info)
    add("functions", cmd_functions, extra=lambda p: (p.add_argument("--filter"), p.add_argument("--limit", type=int)))
    pd = sub.add_parser("decompile"); pd.add_argument("bin"); pd.add_argument("func", nargs="+")
    pd.add_argument("--il", choices=["pseudoc", "hlil", "mlil", "disasm"], default="pseudoc")
    pd.add_argument("--raw", action="store_true"); pd.set_defaults(_fn=cmd_decompile)
    px = sub.add_parser("xrefs"); px.add_argument("bin"); px.add_argument("func"); px.add_argument("--raw", action="store_true"); px.set_defaults(_fn=cmd_xrefs)
    pc = sub.add_parser("callees"); pc.add_argument("bin"); pc.add_argument("func"); pc.add_argument("--raw", action="store_true"); pc.set_defaults(_fn=cmd_callees)
    ps = sub.add_parser("strings"); ps.add_argument("bin"); ps.add_argument("--filter"); ps.add_argument("--min", type=int, default=4); ps.add_argument("--raw", action="store_true"); ps.set_defaults(_fn=cmd_strings)
    pg = sub.add_parser("grepstr"); pg.add_argument("bin"); pg.add_argument("regex"); pg.add_argument("--raw", action="store_true"); pg.set_defaults(_fn=cmd_grepstr)
    add("imports", cmd_imports); add("exports", cmd_exports); add("sections", cmd_sections)
    pa = sub.add_parser("at"); pa.add_argument("bin"); pa.add_argument("addr"); pa.add_argument("--raw", action="store_true"); pa.set_defaults(_fn=cmd_at)

    a = ap.parse_args()
    # normalize the single-func nargs=1 lists
    if hasattr(a, "func") and isinstance(a.func, list) and a._fn is not cmd_decompile:
        a.func = a.func[0]
    bv = load_bv(a.bin)
    a._fn(bv, a)


if __name__ == "__main__":
    main()
