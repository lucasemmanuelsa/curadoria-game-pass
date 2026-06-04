// Scroll track helper
function scrollTrack(trackId, direction) {
  const track = document.getElementById(trackId);
  if (!track) return;
  const cardWidth = track.children[0]?.offsetWidth || 220;
  const scrollAmount = (cardWidth + 20) * 2;
  track.scrollBy({ left: direction * scrollAmount, behavior: 'smooth' });
}

// Show/hide scroll buttons based on scroll position
function updateScrollButtons(wrapper) {
  const track = wrapper.querySelector('[id]');
  if (!track) return;
  const leftBtn = wrapper.querySelector('.scroll-left, .row-left');
  const rightBtn = wrapper.querySelector('.scroll-right, .row-right');
  if (leftBtn) leftBtn.style.opacity = track.scrollLeft > 20 ? '1' : '0.3';
  if (rightBtn) {
    const atEnd = track.scrollLeft + track.clientWidth >= track.scrollWidth - 20;
    rightBtn.style.opacity = atEnd ? '0.3' : '1';
  }
}

// Observe all scroll wrappers
document.querySelectorAll('.featured-scroll-wrapper, .row-scroll-wrapper').forEach(wrapper => {
  const track = wrapper.querySelector('[id]');
  if (track) {
    track.addEventListener('scroll', () => updateScrollButtons(wrapper), { passive: true });
    updateScrollButtons(wrapper);
  }
});

// Scroll reveal animation for sections
const revealObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('revealed');
      revealObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.1 });

document.querySelectorAll('.section').forEach(section => {
  section.style.opacity = '0';
  section.style.transform = 'translateY(30px)';
  section.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
  revealObserver.observe(section);
});

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.section.revealed').forEach(s => {
    s.style.opacity = '1';
    s.style.transform = 'none';
  });
});

// Add revealed class styles inline via JS
const style = document.createElement('style');
style.textContent = `.section.revealed { opacity: 1 !important; transform: translateY(0) !important; }`;
document.head.appendChild(style);
