cat > /home/claude/campusconnect/static/js/charts.js << 'EOF'
// Charts and data visualization

// Simple attendance chart using Canvas
function drawAttendanceChart(canvasId, data) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  
  const ctx = canvas.getContext('2d');
  const width = canvas.width;
  const height = canvas.height;
  const padding = 40;
  
  ctx.clearRect(0, 0, width, height);
  
  // Draw axes
  ctx.strokeStyle = '#e2e8f0';
  ctx.lineWidth = 1;
  ctx.beginPath();
  ctx.moveTo(padding, height - padding);
  ctx.lineTo(width - padding, height - padding);
  ctx.stroke();
  
  // Draw bars
  const barWidth = (width - padding * 2) / data.length - 5;
  const maxValue = Math.max(...data.map(d => d.value));
  
  data.forEach((item, index) => {
    const x = padding + index * (barWidth + 5);
    const barHeight = (item.value / maxValue) * (height - padding * 2);
    const y = height - padding - barHeight;
    
    ctx.fillStyle = item.color || '#1a56db';
    ctx.fillRect(x, y, barWidth, barHeight);
    
    ctx.fillStyle = '#64748b';
    ctx.font = '10px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(item.label, x + barWidth / 2, height - 10);
  });
}

// Pie chart (simplified)
function drawPieChart(canvasId, data) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  
  const ctx = canvas.getContext('2d');
  const width = canvas.width;
  const height = canvas.height;
  const centerX = width / 2;
  const centerY = height / 2;
  const radius = Math.min(width, height) / 2 - 10;
  
  const total = data.reduce((sum, item) => sum + item.value, 0);
  let currentAngle = -Math.PI / 2;
  
  data.forEach(item => {
    const sliceAngle = (item.value / total) * 2 * Math.PI;
    
    ctx.fillStyle = item.color;
    ctx.beginPath();
    ctx.arc(centerX, centerY, radius, currentAngle, currentAngle + sliceAngle);
    ctx.lineTo(centerX, centerY);
    ctx.fill();
    
    currentAngle += sliceAngle;
  });
}

// Animated counter
function animateCounter(element, target) {
  let current = 0;
  const increment = target / 30;
  const timer = setInterval(() => {
    current += increment;
    if (current >= target) {
      element.textContent = target;
      clearInterval(timer);
    } else {
      element.textContent = Math.floor(current);
    }
  }, 30);
}

// Initialize charts on page load
document.addEventListener('DOMContentLoaded', function() {
  // Find and draw all charts
  document.querySelectorAll('[data-chart-type]').forEach(canvas => {
    const type = canvas.dataset.chartType;
    // Charts can be initialized here if data is available
  });
});