---
name: trigger-django-bug
tags: [trigger]
runs: 2
max_turns: 3
timeout_seconds: 180
allowed_tools: [Read, Skill]
---

My Django view crashes with a 500 when the `page` query parameter is missing:

```python
def products(request):
    page = int(request.GET['page'])
    return render(request, 'list.html', {'items': Product.objects.all()[page*20:(page+1)*20]})
```
Fix it.
