from jinja2 import Environment, pass_context
from django.templatetags.static import static
from django.urls import reverse
from django.contrib.messages import get_messages
from django.middleware.csrf import get_token
from django.utils.html import format_html


@pass_context
def csrf_input(context):
    request = context.get('request')
    if request is None:
        return ''
    token = get_token(request)
    return format_html('<input type="hidden" name="csrfmiddlewaretoken" value="{}">', token)


@pass_context
def csrf_token_func(context):
    request = context.get('request')
    if request is None:
        return ''
    return get_token(request)


def url_reverse(name, *args, **kwargs):
    """Wrapper around Django's reverse() that supports both positional and keyword arguments in Jinja2 templates."""
    if args:
        return reverse(name, args=args)
    if kwargs:
        return reverse(name, kwargs=kwargs)
    return reverse(name)


def environment(**options):
    env = Environment(**options)
    env.globals.update({
        'static': static,
        'url': url_reverse,
        'get_messages': get_messages,
        'csrf_input': csrf_input,
        'csrf_token': csrf_token_func,
    })
    env.filters['currency'] = lambda value: f"${value:,.2f}" if value is not None else "$0.00"
    env.filters['date_fmt'] = lambda value, fmt='%d %b %Y': value.strftime(fmt) if value else ''
    env.filters['status_badge'] = status_badge_filter
    # Jinja2 doesn't have replace built-in as a filter in all versions — ensure it exists
    if 'replace' not in env.filters:
        env.filters['replace'] = lambda s, old, new: str(s).replace(old, new)
    return env


def status_badge_filter(status):
    mapping = {
        # Project statuses
        'Active': 'success', 'Completed': 'primary', 'Planning': 'info',
        'On Hold': 'warning', 'Cancelled': 'danger',
        # Attendance
        'Present': 'success', 'Absent': 'danger', 'Late': 'warning', 'Half-Day': 'info',
        # Leave
        'Pending': 'warning', 'Approved': 'success', 'Rejected': 'danger',
        # Payroll
        'Draft': 'secondary', 'Generated': 'info', 'Paid': 'success',
        # Tasks
        'To-Do': 'secondary', 'In Progress': 'primary', 'Review': 'warning', 'Done': 'success',
        # Task priority
        'Low': 'success', 'Medium': 'info', 'High': 'warning', 'Critical': 'danger',
        # Assets
        'Available': 'success', 'Assigned': 'primary', 'Disposed': 'danger', 'Under Repair': 'warning',
    }
    color = mapping.get(status, 'secondary')
    return f'<span class="badge bg-{color}">{status}</span>'
