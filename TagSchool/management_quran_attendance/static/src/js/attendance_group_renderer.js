odoo.define('management_quran_attendance.attendance_group_renderer', function (require) {
    'use strict';

    const ListRenderer = require('web.ListRenderer');
    ؤ
    ListRenderer.include({
        getAttendanceDayNameCells(group) {
            const isAttendanceGroup = group && group.record && group.list && group.list.model === 'attendance.register';
            if (!isAttendanceGroup) {
                return [];
            }

            const record = group.record;
            const year = Number(record.data && record.data.year ? record.data.year : record.year || 0);
            const month = Number(record.data && record.data.month ? record.data.month : record.month || 0);

            if (!year || !month) {
                return [];
            }

            const daysInMonth = new Date(year, month, 0).getDate();
            const labels = [];

            for (let day = 1; day <= daysInMonth; day++) {
                const date = new Date(year, month - 1, day);
                labels.push({
                    number: day,
                    name: date.toLocaleDateString('en-US', { weekday: 'short' }),
                });
            }

            return labels;
        },
    });
});
