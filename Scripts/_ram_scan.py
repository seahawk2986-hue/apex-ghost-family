"""THE RAM-TOP SCAN (the honest visibility): the box's top-consumers."""
import psutil

vm = psutil.virtual_memory()
print(f"[ram-top] {vm.available/2**30:.1f}GB free / {vm.total/2**30:.0f}GB "
      f"({vm.percent}% used)")
tops = sorted(psutil.process_iter(['name', 'memory_info']),
              key=lambda p: -(p.info['memory_info'].rss
                              if p.info['memory_info'] else 0))[:8]
for p in tops:
    mi = p.info['memory_info']
    if mi:
        print(f"  {str(p.info['name'])[:30]:30} {mi.rss/2**30:.2f}GB")