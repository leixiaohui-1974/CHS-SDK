
// CHS-SDK 报告交互功能
document.addEventListener('DOMContentLoaded', function() {
    // 平滑滚动
    const links = document.querySelectorAll('a[href^="#"]');
    links.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // 图表点击放大
    const charts = document.querySelectorAll('.chart-image');
    charts.forEach(chart => {
        chart.addEventListener('click', function() {
            // 可以添加图表放大功能
            console.log('Chart clicked:', this.alt);
        });
    });
    
    // 打印功能
    if (window.location.search.includes('print=true')) {
        window.print();
    }
});
        