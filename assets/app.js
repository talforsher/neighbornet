
function $(q,el=document){return el.querySelector(q)}
function $all(q,el=document){return Array.from(el.querySelectorAll(q))}
function normalize(s){return (s||'').toLowerCase()}

// WordPress Image Processing - Select single image from pipe-separated options
function processWordPressImages() {
  // Process all images, including cards and hero
  const images = $all('img');

  images.forEach(img => {
    // Use original attribute if available to avoid auto-encoding differences
    const attrSrc = img.getAttribute('src') || '';
    const src = attrSrc || img.src;
    const alt = img.alt;
    
    // Normalize possible encoded pipes to a single separator
    const normalizedSrc = src.replace(/%7C/gi, '|');
    
    // Check if src contains pipe-separated URLs (WordPress image options)
    if (normalizedSrc.includes('|')) {
      const imageUrls = normalizedSrc.split('|').map(url => url.trim()).filter(url => url);
      const altTexts = alt.split('|').map(text => text.trim()).filter(text => text);
      
      if (imageUrls.length > 0) {
        // Select the first (usually best) image option
        const selectedUrl = imageUrls[0];
        const selectedAlt = altTexts[0] || '';
        
        // Update the image src and alt to use only the selected option
        img.src = selectedUrl;
        img.alt = selectedAlt;
        
        // Optional: Add click to open in modal for better viewing
        img.style.cursor = 'pointer';
        img.addEventListener('click', () => openImageModal(selectedUrl, selectedAlt));
      }
    }
  });
}

function openImageModal(src, alt) {
  // Create modal if it doesn't exist
  let modal = $('#image-modal');
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'image-modal';
    modal.className = 'image-modal';
    modal.innerHTML = `
      <div class="modal-content">
        <span class="modal-close">&times;</span>
        <img class="modal-image" src="" alt="">
      </div>
    `;
    document.body.appendChild(modal);
    
    // Close modal functionality
    modal.querySelector('.modal-close').addEventListener('click', closeImageModal);
    modal.addEventListener('click', (e) => {
      if (e.target === modal) closeImageModal();
    });
    
    // ESC key to close
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && modal.style.display === 'block') {
        closeImageModal();
      }
    });
  }
  
  // Set image and show modal
  const modalImg = modal.querySelector('.modal-image');
  modalImg.src = src;
  modalImg.alt = alt;
  modal.style.display = 'block';
  document.body.style.overflow = 'hidden';
}

function closeImageModal() {
  const modal = $('#image-modal');
  if (modal) {
    modal.style.display = 'none';
    document.body.style.overflow = 'auto';
  }
}

function filterCards(){
  const q = normalize($('#q').value);
  const cat = normalize($('#cat').value);
  $all('.card').forEach(c=>{
    const text = c.dataset.search;
    const categories = c.dataset.categories || '';
    const okQ = !q || text.includes(q);
    const okC = !cat || categories.includes(cat);
    c.style.display = (okQ && okC) ? '' : 'none';
  });
}

// Initialize everything when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  // Process WordPress images (select single image from pipe-separated options)
  processWordPressImages();
  
  // Set up search functionality if elements exist
  const searchInput = $('#q');
  const categorySelect = $('#cat');
  
  if (searchInput) {
    searchInput.addEventListener('input', filterCards);
  }
  
  if (categorySelect) {
    categorySelect.addEventListener('change', filterCards);
  }

  // Run initial filter to normalize visibility on first load
  if (searchInput || categorySelect) {
    filterCards();
  }
});
