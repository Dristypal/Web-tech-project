cat > /home/claude/campusconnect/static/js/main.js << 'EOF'
// Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
  // Auto-hide flash messages
  const flashes = document.querySelectorAll('.flash');
  flashes.forEach(flash => {
    setTimeout(() => {
      flash.style.opacity = '0';
      setTimeout(() => flash.remove(), 300);
    }, 3000);
  });

  // Active nav item
  const currentPath = window.location.pathname;
  document.querySelectorAll('.nav-item').forEach(item => {
    if (item.href.includes(currentPath)) {
      item.classList.add('active');
    }
  });
});

// Chart data
function createAttendanceChart() {
  const canvas = document.getElementById('attendanceChart');
  if (!canvas) return;
  
  const months = ['Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'Jan', 'Feb'];
  const data = [78, 82, 90, 85, 88, 91, 87];
  
  const ctx = canvas.getContext('2d');
  const width = canvas.width;
  const height = canvas.height;
  
  ctx.clearRect(0, 0, width, height);
  
  const barWidth = width / months.length - 8;
  const maxHeight = height - 40;
  
  data.forEach((val, i) => {
    const barHeight = (val / 100) * maxHeight;
    const x = i * (barWidth + 8) + 4;
    const y = height - barHeight - 20;
    
    ctx.fillStyle = val >= 85 ? '#1a56db' : val >= 75 ? '#f59e0b' : '#ef4444';
    ctx.fillRect(x, y, barWidth, barHeight);
    
    ctx.fillStyle = '#64748b';
    ctx.font = '10px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(months[i], x + barWidth / 2, height - 4);
  });
}

// Initialize on page load
window.addEventListener('load', createAttendanceChart);