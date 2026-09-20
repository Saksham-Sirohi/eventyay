Logging and notifications
=========================

As eventyay is handling monetary transactions, we are very careful to make it possible to review all changes
in the system that lead to the current state.

.. _`logging`:

Logging changes
---------------

We log data changes to the database in a format that makes it possible to display those logs to a human, if
required. eventyay stores all those logs centrally in a model called :py:class:`eventyay.base.models.LogEntry`.
We recommend all relevant models to inherit from ``LoggedModel`` as it simplifies creating new log entries:

.. autoclass:: eventyay.base.models.LoggedModel
   :members: log_action, all_logentries

To actually log an action, you can just call the ``log_action`` method on your object:

.. code-block:: python

   order.log_action('eventyay.event.order.canceled', user=user, data={})

The positional ``action`` argument should represent the type of action and should be globally unique, we
recommend to prefix it with your package name, e.g. ``paypal.payment.rejected``. The ``user`` argument is
optional and may contain the user who performed the action. The optional ``data`` argument can contain
additional information about this action.

Logging form actions
""""""""""""""""""""

A very common use case is to log the changes to a model that have been done in a ``ModelForm``. In this case,
we generally use a custom ``form_valid`` method on our ``FormView`` that looks like this:

.. code-block:: python

    @transaction.atomic
    def form_valid(self, form):
        if form.has_changed():
            self.request.event.log_action('eventyay.event.changed', user=self.request.user, data={
                k: getattr(self.request.event, k) for k in form.changed_data
            })
        messages.success(self.request, _('Your changes have been saved.'))
        return super().form_valid(form)

It gets a little bit more complicated if your form allows file uploads:

.. code-block:: python

    @transaction.atomic
    def form_valid(self, form):
        if form.has_changed():
            self.request.event.log_action(
                'eventyay.event.changed', user=self.request.user, data={
                    k: (form.cleaned_data.get(k).name
                        if isinstance(form.cleaned_data.get(k), File)
                        else form.cleaned_data.get(k))
                    for k in form.changed_data
                }
            )
        messages.success(self.request, _('Your changes have been saved.'))
        return super().form_valid(form)


Displaying logs
"""""""""""""""

If you want to display the logs of a particular object to a user in the backend, you can use the
following ready-to-include template::

   {% include "eventyaycontrol/includes/logs.html" with obj=order %}

We now need a way to translate the action codes like ``eventyay.event.changed`` into human-readable
strings. The :py:attr:`eventyay.base.signals.logentry_display` signals allows you to do so. A simple
implementation could look like:

.. code-block:: python

    from django.utils.translation import gettext as _
    from eventyay.base.signals import logentry_display

    @receiver(signal=logentry_display)
    def eventyaycontrol_logentry_display(sender, logentry, **kwargs):
        plains = {
            'eventyay.event.order.paid': _('The order has been marked as paid.'),
            'eventyay.event.order.refunded': _('The order has been refunded.'),
            'eventyay.event.order.canceled': _('The order has been canceled.'),
            ...
        }
        if logentry.action_type in plains:
            return plains[logentry.action_type]

Sending notifications
---------------------

If you think that the logged information might be important or urgent enough to send out a notification to interested
organizers. In this case, you should listen for the :py:attr:`eventyay.base.signals.register_notification_types` signal
to register a notification type:

.. code-block:: python

    @receiver(register_notification_types)
    def register_my_notification_types(sender, **kwargs):
        return [MyNotificationType(sender)]

Note that this event is different than other events send out by eventyay: ``sender`` may be an event or ``None``. The
latter case is required to let the user define global notification preferences for all events.

You also need to implement a custom class that specifies how notifications should be handled for your notification type.
You should subclass the base ``NotificationType`` class and implement all its members:

.. autoclass:: eventyay.base.notifications.NotificationType
   :members: action_type, verbose_name, required_permission, build_notification

A simple implementation could look like this:

.. code-block:: python

    class MyNotificationType(NotificationType):
        required_permission = "can_view_orders"
        action_type = "eventyay.event.order.paid"
        verbose_name = _("Order has been paid")

        def build_notification(self, logentry: LogEntry):
            order = logentry.content_object

            order_url = build_absolute_uri(
                'control:event.order',
                kwargs={
                    'organizer': logentry.event.organizer.slug,
                    'event': logentry.event.slug,
                    'code': order.code
                }
            )

            n = Notification(
                event=logentry.event,
                title=_('Order {code} has been marked as paid').format(code=order.code),
                url=order_url
            )
            n.add_attribute(_('Order code'), order.code)
            n.add_action(_('View order details'), order_url)
            return n

As you can see, the relevant code is in the ``build_notification`` method that is supposed to create a ``Notification``
method that has a title, description, URL, attributes, and actions. The full definition of ``Notification`` is the
following:

.. autoclass:: eventyay.base.notifications.Notification
   :members: add_action, add_attribute


Logging technical information
-----------------------------

If you just want to log technical information to a log file on disk that does not need to be parsed
and displayed later, you can just use Python's ``logging`` module:

.. code-block:: python

   import logging

   logger = logging.getLogger(__name__)

   logger.info('Startup complete.')

This is also very useful to provide debugging information when an exception occurs:

.. code-block:: python

   try:
      foo()
   except:
      logger.exception('Error when calling foo()')  # Traceback will automatically be appended
      messages.error(request, _('An error occured.'))


Operational logs (privacy-safe)
-------------------------------

Most product areas already persist an audit trail as :class:`LogEntry`
via ``log_action`` (tickets ``LoggingMixin`` and talk/video/mail ``LogMixin``).
The process logger **mirrors** allowlisted ``log_action`` types. Unexpected
faults still use ``logger.exception`` / ``logger.error``. ``log_event`` only
attaches allowlisted extra fields (IDs, outcome, correlation); it is not a
second logging framework. Call sites do not need a helper in every file.

Each operational line includes:

- An ISO-8601 UTC ``datetime``
- ``component`` (``tickets``, ``talk``, ``video``, ``mail``, ``plugins``, ``core``)
- ``outcome=success`` or ``outcome=failure``
- ``action`` (the ``log_action`` type, or a choke-point name such as ``cart.error``)
- Opaque IDs only: ``event_id``, ``order_id``, ``order_code``, ``user_id``, ``object_id``, ``voucher_id``
- Correlation IDs: ``request_id`` (HTTP ``X-Request-ID`` or generated) and ``job_id`` (Celery task id)

Do **not** log emails, names, phones, addresses, payment instrument data,
tokens, cookies, API keys, webhook secrets, voucher secrets, or raw
request/response bodies. ``log_action`` ``data`` payloads are never copied
to the process log. Only allowlisted keys such as ``provider`` (payment
provider identifier) and numeric IDs are promoted onto the log line.

Levels: ``INFO`` for successful lifecycle transitions, ``WARNING`` for
expected business failures, ``ERROR`` (via ``logger.exception``) only for
unexpected faults.

Skipped to keep volume low: scanner heartbeat ``eventyay.device.updated``,
generic ``eventyay.event.settings`` saves, organizer/order comments (not
submission review comments), successful HTTP 2xx/4xx (except 401/403),
and health-check **success** (probes). Page views and join/leave chat are
not mirrored.

Areas:

- **tickets**: attendee cart/checkout/order/payment/refund, products,
  quotas, vouchers, waiting list, check-in, devices/gates, payment-provider
  config, ticket/badge PDF layouts.
- **talk**: speaker/attendee CfP and submissions, reviews, schedule
  publish, tracks, access codes, organizer event/talk-data updates,
  public schedule and schedule-editor HTTP failures (status only, no
  JSON/PII).
- **video**: room lifecycle (via ``log_action``), live WebSocket connect/abnormal
  close, BBB HTTP get/post (no response bodies or join URLs), Janus WebSocket
  connect, WHEP connect, interpretation listener-token, chat webhook
  delivery, Etherpad pad create, and browser-reported failures
  (iframe/HLS/BBB/Jitsi/Janus/Zoom/schedule fav) via ``event.client_log``.
- **mail**: order-email actions, queued mail sent, organizer follower
  notifications, send success/failure without recipient addresses or
  subjects/bodies.
- **plugins**: plugin enable/disable, outbound webhook status/duration
  (no URL/body), inbound Stripe signature validation outcome only.
- **core**: request 401/403/5xx (route name, status, duration), control and
  common login without credentials, team/invite/clone/2FA, Celery job
  failure (task name, not args).

Production format (console handler ``verbose``)::

    LEVEL <iso-8601-utc> eventyay.<component>: <component>.<action> <success|failure> datetime=... component=... outcome=... action=... [error_code=...] [event_id=...] [order_code=...] [request_id=...] [job_id=...]

Examples (PII-free)::

    INFO 2026-09-20T15:45:01Z eventyay.tickets: tickets.eventyay.event.order.placed success datetime=2026-09-20T15:45:01Z component=tickets outcome=success action=eventyay.event.order.placed event_id=12 order_id=34 order_code=ABC12 model=Order request_id=req-7f3a9c

    INFO 2026-09-20T15:45:08Z eventyay.tickets: tickets.eventyay.event.order.paid success datetime=2026-09-20T15:45:08Z component=tickets outcome=success action=eventyay.event.order.paid event_id=12 order_id=34 order_code=ABC12 model=Order request_id=req-7f3a9c

    INFO 2026-09-20T15:45:04Z eventyay.tickets: tickets.eventyay.event.order.payment.started success datetime=2026-09-20T15:45:04Z component=tickets outcome=success action=eventyay.event.order.payment.started event_id=12 order_code=ABC12 payment_provider=stripe payment_id=88 payment_local_id=2 request_id=req-7f3a9c

    INFO 2026-09-20T15:45:05Z eventyay.tickets: tickets.payment.handoff success datetime=2026-09-20T15:45:05Z component=tickets outcome=success action=payment.handoff event_id=12 payment_provider=stripe request_id=req-7f3a9c

    WARNING 2026-09-20T15:45:06Z eventyay.tickets: tickets.eventyay.event.order.payment.failed failure datetime=2026-09-20T15:45:06Z component=tickets outcome=failure action=eventyay.event.order.payment.failed event_id=12 order_code=ABC12 payment_provider=stripe request_id=req-7f3a9c

    INFO 2026-09-20T15:46:01Z eventyay.tickets: tickets.eventyay.event.order.canceled success datetime=2026-09-20T15:46:01Z component=tickets outcome=success action=eventyay.event.order.canceled event_id=12 order_code=ABC12 user_id=9 is_orga_action=True request_id=req-7f3a9c

    INFO 2026-09-20T15:46:10Z eventyay.tickets: tickets.eventyay.event.order.refunded success datetime=2026-09-20T15:46:10Z component=tickets outcome=success action=eventyay.event.order.refunded event_id=12 order_code=ABC12 request_id=req-7f3a9c

    INFO 2026-09-20T16:00:00Z eventyay.tickets: tickets.eventyay.event.checkin success datetime=2026-09-20T16:00:00Z component=tickets outcome=success action=eventyay.event.checkin event_id=12 checkin_list_id=5 position_id=77 request_id=req-7f3a9c

    WARNING 2026-09-20T16:00:02Z eventyay.tickets: tickets.checkin.error failure datetime=2026-09-20T16:00:02Z component=tickets outcome=failure action=checkin.error error_code=already_redeemed event_id=12 request_id=req-7f3a9c

    INFO 2026-09-20T15:44:50Z eventyay.tickets: tickets.voucher.apply success datetime=2026-09-20T15:44:50Z component=tickets outcome=success action=voucher.apply event_id=12 job_id=c0ffee12-task

    WARNING 2026-09-20T15:44:40Z eventyay.tickets: tickets.cart.error failure datetime=2026-09-20T15:44:40Z component=tickets outcome=failure action=cart.error error_code=cart_error event_id=12 request_id=req-7f3a9c

    WARNING 2026-09-20T15:44:41Z eventyay.tickets: tickets.checkout.cart_invalid failure datetime=2026-09-20T15:44:41Z component=tickets outcome=failure action=checkout.cart_invalid error_code=cart_invalid event_id=12 request_id=req-7f3a9c

    INFO 2026-09-20T16:10:00Z eventyay.talk: talk.eventyay.submission.create success datetime=2026-09-20T16:10:00Z component=talk outcome=success action=eventyay.submission.create event_id=12 object_id=99 request_id=req-7f3a9c

    INFO 2026-09-20T16:11:00Z eventyay.talk: talk.eventyay.schedule.release success datetime=2026-09-20T16:11:00Z component=talk outcome=success action=eventyay.schedule.release event_id=12 request_id=req-7f3a9c

    WARNING 2026-09-20T16:12:00Z eventyay.video: video.janus.connection failure datetime=2026-09-20T16:12:00Z component=video outcome=failure action=janus.connection error_code=janus_error request_id=req-7f3a9c

    INFO 2026-09-20T16:12:05Z eventyay.video: video.connection.get success datetime=2026-09-20T16:12:05Z component=video outcome=success action=connection.get backend=bbb status=200 duration_ms=88 event_id=12

    WARNING 2026-09-20T16:12:08Z eventyay.video: video.client.iframe.error failure datetime=2026-09-20T16:12:08Z component=video outcome=failure action=client.iframe.error error_code=iframe_error backend=bbb event_id=12 user_id=9

    INFO 2026-09-20T16:13:00Z eventyay.mail: mail.mail.send success datetime=2026-09-20T16:13:00Z component=mail outcome=success action=mail.send event_id=12 order_id=34 mail_type=order job_id=c0ffee12-task

    WARNING 2026-09-20T16:13:02Z eventyay.mail: mail.eventyay.event.order.email.error failure datetime=2026-09-20T16:13:02Z component=mail outcome=failure action=eventyay.event.order.email.error event_id=12 order_code=ABC12 job_id=c0ffee12-task

    INFO 2026-09-20T16:14:00Z eventyay.plugins: plugins.webhook.outbound success datetime=2026-09-20T16:14:00Z component=plugins outcome=success action=webhook.outbound webhook_id=8 status=200 duration_ms=41 retry_count=0 job_id=c0ffee12-task

    WARNING 2026-09-20T16:15:00Z eventyay.core: core.permission.denied failure datetime=2026-09-20T16:15:00Z component=core outcome=failure action=permission.denied error_code=forbidden status=403 user_id=9 request_id=req-7f3a9c

    INFO 2026-09-20T16:16:00Z eventyay.core: core.eventyay.team.created success datetime=2026-09-20T16:16:00Z component=core outcome=success action=eventyay.team.created object_id=3 is_orga_action=True request_id=req-7f3a9c

    INFO 2026-09-20T16:16:10Z eventyay.talk: talk.eventyay.event.update success datetime=2026-09-20T16:16:10Z component=talk outcome=success action=eventyay.event.update event_id=12 is_orga_action=True request_id=req-7f3a9c

    WARNING 2026-09-20T16:17:00Z eventyay.talk: talk.schedule.save failure datetime=2026-09-20T16:17:00Z component=talk outcome=failure action=schedule.save error_code=http_error backend=schedule_editor status=500
