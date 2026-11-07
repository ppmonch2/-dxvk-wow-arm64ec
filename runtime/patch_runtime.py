#!/usr/bin/env python3
"""Port only the WoW copyable-syscall + thread-exit grace changes to Wine 11.

Wine 11 already includes suspend/exception fixes carried in the old Wine 10
patch. Do not reapply that whole patch or mix Wine 10 binaries into Wine 11.
Run after the upstream Android/GE patch lists, before compiling.
"""
import pathlib
import subprocess
import sys


def replace(path, old, new):
    data = path.read_text()
    if data.count(old) != 1:
        raise RuntimeError(f'{path}: expected exactly one matching source block')
    path.write_text(data.replace(old, new))


def main(root):
    replace(root / 'include/wine/asm.h',
            '"ldr x16, 1f\\n\\t" \\\n                       "ldr x16, [x16]\\n\\t"',
            '"ldr x16, [x18, #0x2f8]\\n\\t" \\\n                       "nop\\n\\t"')
    replace(root / 'include/wine/asm.h',
            '"1:\\t.quad " __ASM_NAME("__wine_syscall_dispatcher") )',
            '".quad 0" )')
    path = root / 'dlls/ntdll/unix/signal_arm64.c'
    replace(path, 'struct arm64_thread_data\n{\n    BOOL suspend_pending;\n};',
            'struct arm64_thread_data\n{\n    BOOL suspend_pending;\n'
            '    void *syscall_dispatcher; /* WOW-PROTON11: copyable native ARM64 stubs */\n};')
    anchor = 'C_ASSERT( sizeof(struct arm64_thread_data) <= sizeof(((struct ntdll_thread_data *)0)->cpu_data) );'
    replace(path, anchor, anchor + '\nC_ASSERT( offsetof(TEB, GdiTebBatch) + '
            'offsetof(struct ntdll_thread_data, cpu_data) + '
            'offsetof(struct arm64_thread_data, syscall_dispatcher) == 0x2f8 );')
    replace(path, '    context.X0  = (DWORD64)entry;',
            '    /* The target TEB belongs to this new thread; never use a parent TEB. */\n'
            '    ((struct arm64_thread_data *)((struct ntdll_thread_data *)&teb->GdiTebBatch)->cpu_data)'
            '->syscall_dispatcher = __wine_syscall_dispatcher;\n\n'
            '    context.X0  = (DWORD64)entry;')
    path = root / 'dlls/ntdll/thread.c'
    replace(path, 'void WINAPI RtlExitUserThread( ULONG status )\n{\n    ULONG last;',
            'void WINAPI RtlExitUserThread( ULONG status )\n{\n    ULONG last;\n'
            '#ifdef __aarch64__\n'
            '    LARGE_INTEGER grace = { .QuadPart = -1000000 }; /* same 100 ms as P10 control */\n'
            '#endif')
    replace(path, '    if (last) RtlExitUserProcess( status );\n    LdrShutdownThread();',
            '    if (last) RtlExitUserProcess( status );\n'
            '#ifdef __aarch64__\n    NtDelayExecution( FALSE, &grace );\n#endif\n'
            '    LdrShutdownThread();')
    subprocess.run(['git', 'apply', str(pathlib.Path(__file__).with_name('android-owner.patch'))],
                   cwd=root, check=True)
    print('WOW-PROTON11: Wine 11 source patched; dispatcher TEB+0x2f8, grace 100 ms, Android owner')


if __name__ == '__main__':
    main(pathlib.Path(sys.argv[1]).resolve())
