// Static equivalent of the package SVG filter, for file: fixture use.
const params=new URLSearchParams(location.search);
document.body.classList.add(params.get('theme')==='dark'?'dark':'light',params.get('concept')==='a'?'optical':'frosted');
if(document.body.classList.contains('optical')) {
 document.querySelector('.instrument').classList.add('liquid-glass','liquid-glass--subtle');
 document.body.insertAdjacentHTML('beforeend','<svg aria-hidden="true" focusable="false" width="0" height="0"><filter id="liquid-glass-filter" x="-20%" y="-20%" width="140%" height="140%" color-interpolation-filters="sRGB"><feTurbulence type="fractalNoise" baseFrequency="0.008" numOctaves="2" seed="7" result="noise"/><feDisplacementMap in="SourceGraphic" in2="noise" scale="12" xChannelSelector="R" yChannelSelector="G"/></filter></svg>');
}
