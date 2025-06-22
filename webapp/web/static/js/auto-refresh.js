// Auto Refresh on Back Button Navigation
(function() {
    'use strict';
    
    let isNavigatingAway = false;
    let lastVisit = Date.now();
    
    // ตั้งค่า flag เมื่อกำลังจะออกจากหน้า
    window.addEventListener('beforeunload', function() {
      isNavigatingAway = true;
      sessionStorage.setItem('lastVisit', Date.now().toString());
    });
    
    // ตรวจสอบเมื่อกลับมาที่หน้า (กดปุ่มย้อนหน้า)
    window.addEventListener('pageshow', function(event) {
      // ถ้าหน้าถูกโหลดจาก bfcache (กดปุ่มย้อนหน้า)
      if (event.persisted) {
        console.log('Page loaded from bfcache - refreshing...');
        window.location.reload();
        return;
      }
      
      // ตรวจสอบ navigation type
      if (window.performance && window.performance.getEntriesByType) {
        const navEntries = window.performance.getEntriesByType('navigation');
        if (navEntries.length > 0 && navEntries[0].type === 'back_forward') {
          console.log('Back/Forward navigation detected - refreshing...');
          window.location.reload();
          return;
        }
      }
    });
    
    // ตรวจสอบ browser history state changes
    window.addEventListener('popstate', function(event) {
      console.log('Popstate event detected - refreshing...');
      // เพิ่ม delay เล็กน้อยเพื่อให้ browser ประมวลผล
      setTimeout(function() {
        window.location.reload();
      }, 10);
    });
    
    // ตรวจสอบสำหรับ Mobile Safari
    if (/iPad|iPhone|iPod/.test(navigator.userAgent)) {
      window.addEventListener('focus', function() {
        const currentTime = Date.now();
        const lastVisitTime = parseInt(sessionStorage.getItem('lastVisit') || '0');
        
        // ถ้าเวลาผ่านไปมากกว่า 1 วินาที และเคยออกจากหน้า
        if (isNavigatingAway && currentTime - lastVisitTime > 1000) {
          console.log('iOS Safari focus event - refreshing...');
          window.location.reload();
        }
      });
    }
    
    // ตรวจสอบ document visibility (สำหรับ tab switching)
    document.addEventListener('visibilitychange', function() {
      if (!document.hidden && isNavigatingAway) {
        const currentTime = Date.now();
        const lastVisitTime = parseInt(sessionStorage.getItem('lastVisit') || '0');
        
        // ถ้าเวลาผ่านไปมากกว่า 2 วินาที
        if (currentTime - lastVisitTime > 2000) {
          console.log('Visibility change detected - refreshing...');
          window.location.reload();
        }
      }
    });
    
    // Reset flag เมื่อโหลดหน้าเสร็จ
    window.addEventListener('load', function() {
      isNavigatingAway = false;
      sessionStorage.removeItem('lastVisit');
    });
    
    // Prevent caching ให้มากขึ้น
    if (window.history && window.history.pushState) {
      // เพิ่ม timestamp ใน URL เพื่อป้องกัน cache
      const url = new URL(window.location);
      if (!url.searchParams.has('_t')) {
        url.searchParams.set('_t', Date.now().toString());
        window.history.replaceState({}, '', url.toString());
      }
    }
    
  })();