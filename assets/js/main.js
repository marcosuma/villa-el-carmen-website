// Mobile nav toggle
const navToggle = document.getElementById('nav-toggle');
const navContent = document.getElementById('nav-content');
navToggle.addEventListener('click', function () {
    navContent.classList.toggle('hidden');
});

// Smooth scrolling for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        document.querySelector(this.getAttribute('href')).scrollIntoView({
            behavior: 'smooth'
        });
    });
});

// Scroll animations
const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('visible');
        }
    });
}, { threshold: 0.1 });

const elements = document.querySelectorAll('.fade-in-up');
elements.forEach(el => observer.observe(el));

// Dining Carousel Logic
document.addEventListener('DOMContentLoaded', function () {
    const slides = document.querySelectorAll('#dining-carousel .carousel-slide');
    const slidesContainer = document.querySelector('#dining-carousel .carousel-slides');
    const nextBtn = document.getElementById('dining-next');
    const prevBtn = document.getElementById('dining-prev');
    const dotsContainer = document.getElementById('dining-dots');
    let currentSlide = 0;
    let slideInterval;

    if (!slides.length) return;

    // Create dots
    slides.forEach((_, i) => {
        const dot = document.createElement('button');
        dot.classList.add('w-3', 'h-3', 'rounded-full', 'transition-colors', 'duration-300');
        if (i === 0) {
            dot.classList.add('bg-theme-dot-active');
        } else {
            dot.classList.add('bg-theme-dot-inactive');
        }
        dot.addEventListener('click', () => {
            goToSlide(i);
            resetInterval();
        });
        dotsContainer.appendChild(dot);
    });

    const dots = dotsContainer.querySelectorAll('button');

    function goToSlide(slideIndex) {
        slidesContainer.style.transform = `translateX(-${slideIndex * 100}%)`;
        currentSlide = slideIndex;
        updateDots();
    }

    function updateDots() {
        dots.forEach((dot, i) => {
            dot.classList.toggle('bg-theme-dot-active', i === currentSlide);
            dot.classList.toggle('bg-theme-dot-inactive', i !== currentSlide);
        });
    }

    function showNextSlide() {
        const nextSlide = (currentSlide + 1) % slides.length;
        goToSlide(nextSlide);
    }

    function showPrevSlide() {
        const prevSlide = (currentSlide - 1 + slides.length) % slides.length;
        goToSlide(prevSlide);
    }

    function startInterval() {
        slideInterval = setInterval(showNextSlide, 5000); // Change slide every 5 seconds
    }

    function resetInterval() {
        clearInterval(slideInterval);
        startInterval();
    }

    nextBtn.addEventListener('click', () => {
        showNextSlide();
        resetInterval();
    });

    prevBtn.addEventListener('click', () => {
        showPrevSlide();
        resetInterval();
    });

    startInterval();

    // Lightbox functionality
    const clickableImages = document.querySelectorAll('.feature-image-clickable');
    const lightbox = document.getElementById('lightbox');
    const lightboxImage = document.getElementById('lightbox-image');
    const lightboxClose = document.getElementById('lightbox-close');

    clickableImages.forEach(image => {
        image.addEventListener('click', () => {
            const imgSrc = image.getAttribute('src');
            lightboxImage.setAttribute('src', imgSrc);
            lightbox.classList.remove('hidden');
            lightbox.classList.add('flex');
        });
    });

    const closeLightbox = () => {
        lightbox.classList.add('hidden');
        lightbox.classList.remove('flex');
    };

    lightboxClose.addEventListener('click', closeLightbox);
    lightbox.addEventListener('click', (e) => {
        if (e.target === lightbox) {
            closeLightbox();
        }
    });
});


