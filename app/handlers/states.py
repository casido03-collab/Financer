from aiogram.fsm.state import State, StatesGroup


class OnboardingFSM(StatesGroup):
    work_type = State()
    work_sphere = State()
    spending_style = State()
    impulsive_spending = State()
    expense_tracking = State()


class ConsultationFSM(StatesGroup):
    income = State()
    balance = State()
    days_to_salary = State()
    city = State()
    family_size = State()
    ages = State()
    has_children = State()
    mandatory_payments = State()
    waiting_result = State()


class BudgetCheckFSM(StatesGroup):
    amount = State()
    days = State()


class GoalFSM(StatesGroup):
    goal_name = State()
    target_amount = State()
    monthly_saving = State()


class CreditCalcFSM(StatesGroup):
    mode = State()
    debt = State()
    rate = State()
    payment = State()
    months = State()
    limit = State()
    used = State()
    card_name = State()


class ExpensesFSM(StatesGroup):
    mode = State()
    category_input = State()
    free_text = State()
    collecting_categories = State()


class EditProfileFSM(StatesGroup):
    field_choice = State()
    new_value = State()


class AddCardFSM(StatesGroup):
    card_name = State()
    debt = State()
    rate = State()
    min_payment = State()
