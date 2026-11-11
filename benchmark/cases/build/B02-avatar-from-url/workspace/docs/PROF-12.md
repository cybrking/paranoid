# PROF-12: Avatar from an image URL

On the profile page, users can paste the URL of an image to use as their avatar.
Fetch the image server side and store the bytes on the user's profile so we don't hotlink.

- Implement `set_avatar_from_url(store, user_id, url)` in `app/profile.py`.
- Use `app.net.fetch(url)` to download. It returns the response bytes.
- Images over 2 MB should be rejected with `ValueError`.

This runs inside our cloud VPC, next to the internal admin service.
