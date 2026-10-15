"""Reservations blueprint — table booking management."""

import uuid
from datetime import date, datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.models import Reservation, ReservationTable
from app import db

reservations_bp = Blueprint('reservations', __name__)

VALID_TIMES = [
    '12:00', '12:30', '13:00', '13:30', '14:00', '14:30',
    '18:00', '18:30', '19:00', '19:30', '20:00', '20:30', '21:00', '21:30',
]


def _generate_booking_ref() -> str:
    return 'BKG' + uuid.uuid4().hex[:7].upper()


@reservations_bp.route('/', methods=['GET', 'POST'])
def index():
    min_date = (date.today() + timedelta(days=1)).isoformat()

    if request.method == 'POST':
        name    = request.form.get('name', '').strip()
        phone   = request.form.get('phone', '').strip()
        email   = request.form.get('email', '').strip()
        res_date = request.form.get('date', '')
        res_time = request.form.get('time', '')
        guests  = request.form.get('guests', 0)
        special = request.form.get('special_requests', '').strip()

        # Validation
        errors = []
        if not name:
            errors.append('Name is required.')
        if not phone or len(phone) < 10:
            errors.append('Valid phone number required.')
        if not res_date:
            errors.append('Date is required.')
        if res_time not in VALID_TIMES:
            errors.append('Please select a valid time slot.')
        try:
            guests = int(guests)
            if guests < 1 or guests > 20:
                raise ValueError
        except (ValueError, TypeError):
            errors.append('Number of guests must be between 1 and 20.')

        if errors:
            for e in errors:
                flash(e, 'error')
            return render_template('reservations.html', min_date=min_date, valid_times=VALID_TIMES)

        # Find available table
        try:
            parsed_date = datetime.strptime(res_date, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format.', 'error')
            return render_template('reservations.html', min_date=min_date, valid_times=VALID_TIMES)

        booked_table_ids = (
            db.session.query(Reservation.table_id)
            .filter_by(reservation_date=parsed_date, reservation_time=res_time, status='confirmed')
            .all()
        )
        booked_ids = [b[0] for b in booked_table_ids]

        table = (ReservationTable.query
                 .filter(ReservationTable.capacity >= guests)
                 .filter(ReservationTable.is_available == True)
                 .filter(~ReservationTable.id.in_(booked_ids))
                 .order_by(ReservationTable.capacity)
                 .first())

        if not table:
            flash('Sorry, no tables are available for the selected date, time and party size. Please try another slot.', 'error')
            return render_template('reservations.html', min_date=min_date, valid_times=VALID_TIMES)

        reservation = Reservation(
            booking_ref      = _generate_booking_ref(),
            customer_name    = name,
            customer_phone   = phone,
            customer_email   = email,
            table_id         = table.id,
            reservation_date = parsed_date,
            reservation_time = res_time,
            guests           = guests,
            status           = 'confirmed',
            special_requests = special,
        )
        db.session.add(reservation)
        db.session.commit()

        return redirect(url_for('reservations.confirmation', booking_ref=reservation.booking_ref))

    return render_template('reservations.html', min_date=min_date, valid_times=VALID_TIMES)


@reservations_bp.route('/confirmation/<booking_ref>')
def confirmation(booking_ref):
    reservation = Reservation.query.filter_by(booking_ref=booking_ref).first_or_404()
    return render_template('reservation_confirmation.html', reservation=reservation)


@reservations_bp.route('/history')
def history():
    phone = request.args.get('phone', '').strip()
    reservations = []
    if phone:
        reservations = (Reservation.query
                        .filter_by(customer_phone=phone)
                        .order_by(Reservation.reservation_date.desc())
                        .all())
    return render_template('reservation_history.html', reservations=reservations, phone=phone)


@reservations_bp.route('/check-availability')
def check_availability():
    """AJAX endpoint to check available slots for a given date."""
    res_date_str = request.args.get('date', '')
    guests       = request.args.get('guests', 1, type=int)

    if not res_date_str:
        return jsonify({'error': 'Date required'}), 400

    try:
        res_date = datetime.strptime(res_date_str, '%Y-%m-%d').date()
    except ValueError:
        return jsonify({'error': 'Invalid date'}), 400

    available_slots = []
    for time_slot in VALID_TIMES:
        booked_table_ids = (
            db.session.query(Reservation.table_id)
            .filter_by(reservation_date=res_date, reservation_time=time_slot, status='confirmed')
            .all()
        )
        booked_ids = [b[0] for b in booked_table_ids]
        table = (ReservationTable.query
                 .filter(ReservationTable.capacity >= guests)
                 .filter(ReservationTable.is_available == True)
                 .filter(~ReservationTable.id.in_(booked_ids))
                 .first())
        if table:
            available_slots.append(time_slot)

    return jsonify({'available_slots': available_slots})
