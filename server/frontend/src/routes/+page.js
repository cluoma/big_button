// since there's no dynamic data here, we can prerender
// it so that it gets served as a static asset in production
export const prerender = true;

/** @type {import('./$types').PageLoad} */
export async function load({ fetch }) {
    const response = await fetch('http://bigbutton.cluoma.com/api/button_press');

    return {
        button_presses: await response.json()
    };
}