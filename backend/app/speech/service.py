"""Nothing server-side. Reading aloud happens in the browser.

`frontend/components/layout/ListenButton.tsx` uses the browser's own speech, and only voices that
run on the device: a cloud voice would send the person's result to a speech service. Where no local
voice exists, the button isn't shown. So there is no audio endpoint and no audio to store.
"""
