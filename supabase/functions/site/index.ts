// Supabase serves HTML from Edge Functions and Storage as text/plain on *.supabase.co,
// so this function only redirects to the page on GitHub Pages.
Deno.serve(() => Response.redirect("https://kostadindev.github.io/cambops/", 302));
