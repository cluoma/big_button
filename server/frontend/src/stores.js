import { readable } from 'svelte/store';

/* for deploying */
export const apihost = readable('http://bigbutton.cluoma.com', function start(set) {

    return function stop() {};
});
/* for testing */
// export const apihost = readable('http://127.0.0.1:9898', function start(set) {
//
// 	return function stop() {};
// });