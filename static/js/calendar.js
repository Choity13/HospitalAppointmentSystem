// static/js/calendar.js
document.addEventListener('DOMContentLoaded', function() {
    // Get the calendar grid container element
    const calendarGrid = document.getElementById('calendarGrid');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const noSlotsMessage = document.getElementById('noSlotsMessage');

    // Check if we have the necessary elements to proceed
    if (!calendarGrid) {
        console.error('Calendar grid element not found!');
        return;
    }

    // Extract doctor ID from the data attribute
    const doctorId = calendarGrid.dataset.doctorId;
    const doctorName = calendarGrid.dataset.doctorName;

    if (!doctorId) {
        console.error('Doctor ID not found on calendar grid!');
        return;
    }

    // Initialize the calendar
    initCalendar(doctorId, doctorName);
});

async function initCalendar(doctorId, doctorName) {
    const loadingSpinner = document.getElementById('loadingSpinner');
    const noSlotsMessage = document.getElementById('noSlotsMessage');
    
    try {
        // Show loading spinner
        showSpinner(loadingSpinner, true);
        hideNoSlotsMessage(noSlotsMessage);
        
        // Fetch calendar data
        const response = await fetch(`/patient/calendar/${doctorId}`, {
            headers: {
                'Accept': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error('Failed to fetch calendar data');
        }

        const calendarData = await response.json();
        
        // Process and render the calendar
        renderCalendar(calendarData, doctorName);

    } catch (error) {
        console.error('Error loading calendar:', error);
        showNoSlotsMessage(noSlotsMessage);
    } finally {
        // Hide loading spinner
        showSpinner(loadingSpinner, false);
    }
}

function showSpinner(spinner, show) {
    if (spinner) {
        spinner.style.display = show ? 'block' : 'none';
    }
}

function showNoSlotsMessage(message) {
    if (message) {
        message.style.display = 'block';
    }
}

function hideNoSlotsMessage(message) {
    if (message) {
        message.style.display = 'none';
    }
}

function renderCalendar(calendarData, doctorName) {
    const calendarGrid = document.getElementById('calendarGrid');
    const noSlotsMessage = document.getElementById('noSlotsMessage');
    
    if (!calendarGrid) return;
    
    // Clear any previous content
    calendarGrid.innerHTML = '<div class="card-body"></div>';
    const calendarBody = calendarGrid.querySelector('.card-body');
    
    // Step 1: Collect and sort dates
    const sortedDates = Object.keys(calendarData).sort();
    const limitedDates = sortedDates.slice(0, 10); // Limit to next 10 days (Mon-Fri)

    // Step 2: Collect all unique slot times across all dates
    const allSlotTimes = new Set();
    sortedDates.forEach(dateStr => {
        calendarData[dateStr].forEach(slot => {
            allSlotTimes.add(slot.slot_time);
        });
    });
    const sortedSlotTimes = Array.from(allSlotTimes).sort();

    // Step 3: Render calendar table
    renderTable(limitedDates, sortedSlotTimes, calendarData, doctorName, calendarBody);

    // Check if there are any available slots
    const hasAvailableSlots = limitedDates.some(dateStr => 
        (calendarData[dateStr] || []).some(slot => slot.is_available && !slot.is_booked)
    );
    if (!hasAvailableSlots) {
        showNoSlotsMessage(noSlotsMessage);
    }
}

function renderTable(dates, slotTimes, calendarData, doctorName, container) {
    // Create table
    const table = document.createElement('table');
    table.className = 'table table-bordered';
    const thead = document.createElement('thead');
    const tbody = document.createElement('tbody');

    // Render header row with dates
    const headerRow = document.createElement('tr');
    headerRow.className = 'table-light';
    const emptyHeader = document.createElement('th');
    emptyHeader.textContent = 'Time';
    headerRow.appendChild(emptyHeader);

    dates.forEach(dateStr => {
        const th = document.createElement('th');
        const date = new Date(dateStr + 'T00:00:00');
        const dayName = date.toLocaleDateString('en-US', { weekday: 'short' });
        const dayNum = date.getDate();
        const monthName = date.toLocaleDateString('en-US', { month: 'short' });
        th.textContent = `${dayName} ${dayNum} ${monthName}`;
        headerRow.appendChild(th);
    });

    thead.appendChild(headerRow);

    // Render each time slot row
    slotTimes.forEach(timeStr => {
        const row = document.createElement('tr');
        const timeCell = document.createElement('td');
        timeCell.className = 'fw-semibold';
        timeCell.textContent = timeStr;
        row.appendChild(timeCell);

        dates.forEach(dateStr => {
            const cell = document.createElement('td');
            const slotsOnDate = (calendarData[dateStr] || []).find(slot => slot.slot_time === timeStr);
            if (slotsOnDate) {
                // Slot exists
                const slot = slotsOnDate;
                cell.style.textAlign = 'center';
                cell.style.padding = '8px';

                if (slot.is_booked) {
                    // Booked: red
                    cell.style.backgroundColor = '#dc3545';
                    cell.style.color = 'white';
                    cell.style.cursor = 'not-allowed';
                    cell.setAttribute('title', 'Already booked');
                    cell.innerHTML = '<i class="bi bi-x-circle"></i>';
                } else if (!slot.is_available) {
                    // Unavailable: grey
                    cell.style.backgroundColor = '#adb5bd';
                    cell.style.color = 'white';
                    cell.style.cursor = 'not-allowed';
                    cell.setAttribute('title', 'Unavailable');
                    cell.innerHTML = '<i class="bi bi-dash-circle"></i>';
                } else {
                    // Available: green
                    cell.style.backgroundColor = '#28a745';
                    cell.style.color = 'white';
                    cell.style.cursor = 'pointer';
                    cell.setAttribute('title', 'Click to book');
                    cell.innerHTML = '<i class="bi bi-check-circle"></i>';
                    cell.setAttribute('data-slot-id', slot.slot_id);
                    cell.setAttribute('data-date', dateStr);
                    cell.setAttribute('data-time', slot.slot_time);
                    cell.setAttribute('data-doctor-name', doctorName);

                    // Add click event listener
                    cell.addEventListener('click', function() {
                        openBookingModal(
                            this.getAttribute('data-slot-id'),
                            this.getAttribute('data-doctor-name'),
                            this.getAttribute('data-date'),
                            this.getAttribute('data-time')
                        );
                    });
                }
            } else {
                // No slot for this time/date
                cell.style.backgroundColor = '#f8f9fa';
            }
            row.appendChild(cell);
        });

        tbody.appendChild(row);
    });

    // Append everything to the grid
    table.appendChild(thead);
    table.appendChild(tbody);
    container.appendChild(table);
}

function openBookingModal(slotId, doctorName, date, time) {
    const bookingModalElement = document.getElementById('bookingModal');
    if (!bookingModalElement) return;
    
    const bookingModal = new bootstrap.Modal(bookingModalElement);

    // Populate modal fields
    const modalDoctorName = document.getElementById('modalDoctorName');
    const modalDateTime = document.getElementById('modalDateTime');
    const slotIdInput = document.getElementById('slotIdInput');
    const reasonForVisit = document.getElementById('reasonForVisit');
    const bookingForm = document.getElementById('bookingForm');
    
    if (modalDoctorName) {
        modalDoctorName.value = doctorName;
    }
    if (modalDateTime) {
        modalDateTime.value = `${date} at ${time}`;
    }
    if (slotIdInput) {
        slotIdInput.value = slotId;
    }
    if (reasonForVisit) {
        reasonForVisit.value = '';
    }
    if (bookingForm) {
        bookingForm.action = `/patient/book/${slotId}`;
    }

    bookingModal.show();
}
