// Enhanced workshops filtering with better UX
document.addEventListener('DOMContentLoaded', function() {
    const categoryFilter = document.getElementById('categoryFilter');
    const searchFilter = document.getElementById('searchFilter');
    const skillsFilter = document.getElementById('skillsFilter');
    const statusFilter = document.getElementById('statusFilter');
    const workshopItems = document.querySelectorAll('.workshop-card');
    const noResults = document.getElementById('noResults');

    function filterWorkshops() {
        const categoryValue = categoryFilter.value;
        const searchValue = searchFilter.value.toLowerCase();
        const skillsValue = skillsFilter.value.toLowerCase();
        const statusValue = statusFilter.value;

        let visibleCount = 0;

        workshopItems.forEach(item => {
            const category = item.querySelector('.badge.status-scheduled')?.nextSibling?.textContent?.trim().toLowerCase() || '';
            const status = item.querySelector('.badge.status-scheduled')?.textContent?.toLowerCase().includes('scheduled') ? 'scheduled' : 'other';
            const title = item.querySelector('.card-title').textContent.toLowerCase();
            const description = item.querySelector('.card-text').textContent.toLowerCase();
            const skills = item.textContent.toLowerCase();

            const categoryMatch = !categoryValue || category.includes(categoryValue);
            const statusMatch = statusValue === 'all' || status === 'scheduled';
            const searchMatch = !searchValue || title.includes(searchValue) || description.includes(searchValue);
            const skillsMatch = !skillsValue || skills.includes(skillsValue);

            if (categoryMatch && statusMatch && searchMatch && skillsMatch) {
                item.style.display = 'block';
                visibleCount++;
                // Add fade-in animation
                item.style.animation = 'fadeIn 0.5s ease-in';
            } else {
                item.style.display = 'none';
            }
        });

        // Show/hide no results message
        if (noResults) {
            if (visibleCount === 0 && workshopItems.length > 0) {
                noResults.style.display = 'block';
            } else {
                noResults.style.display = 'none';
            }
        }
    }

    // Add event listeners with debouncing for search
    let searchTimeout;
    searchFilter.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(filterWorkshops, 300);
    });

    categoryFilter.addEventListener('change', filterWorkshops);
    skillsFilter.addEventListener('input', function() {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(filterWorkshops, 300);
    });
    statusFilter.addEventListener('change', filterWorkshops);

    // Add CSS for fade animation
    const style = document.createElement('style');
    style.textContent = `
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
    `;
    document.head.appendChild(style);
});