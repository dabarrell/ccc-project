
var s = 'Sat May 06 13:10:00 +0000 2017';
var d = new Date(Date.parse(s))
console.log(d)
console.log(d.toISOString().slice(0,10) + ' ' + d.toLocaleTimeString())