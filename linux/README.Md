### Service management

To check the status of the systemd servive, just do:

```
systemctl --u status judsound.service
```

Note the `-u` is required because it is a user-level service.

To restart the service, just do:

```
systemctl --u restart judsound.service
```


### Log inspection

To check the log of the judsound system, simply do:

```
journalctl | grep python
```

No need for sudo since we are dealing with a user-level service.

It should report all the `print()` calls from python.
