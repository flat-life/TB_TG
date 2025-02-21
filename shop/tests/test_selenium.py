import pytest
from django.test import LiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.common.by import By
from selenium.webdriver.common.alert import Alert
from time import sleep


@pytest.fixture(scope="class")
def chrome_driver(request):
    options = Options()
    # options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    request.cls.driver = driver
    yield
    driver.quit()


@pytest.mark.django_db
@pytest.mark.usefixtures("chrome_driver")
class TestSelenium(LiveServerTestCase):
    def test_home_page(self):
        try:
            self.driver.get('http://localhost:8000/')
            self.driver.maximize_window()
            sleep(5)
            assert "TB_TG Shop" in self.driver.title
        except Exception as e:
            pytest.fail(f"Test failed: {str(e)}")

    def test_register_and_login(self):
        self.driver.get('http://localhost:8000/')
        self.driver.maximize_window()
        # sleep(5)
        # link = driver.find_element_by_link_text("ورود /ثبت نام")
        # link.click()
        wait = WebDriverWait(self.driver, 10)
        link = wait.until(expected_conditions.element_to_be_clickable((By.CSS_SELECTOR, "a[href='/login/']")))
        link.click()
        link = wait.until(expected_conditions.element_to_be_clickable((By.CSS_SELECTOR, "a[href='/register/']")))
        link.click()

        phone_number_field = wait.until(expected_conditions.presence_of_element_located((By.ID, "phone_number")))
        print(phone_number_field)
        email_field = wait.until(expected_conditions.presence_of_element_located((By.ID, "email")))
        print(email_field)
        password_field = wait.until(expected_conditions.presence_of_element_located((By.ID, "password")))
        print(password_field)
        submit_button = wait.until(expected_conditions.element_to_be_clickable((By.XPATH, "//button[@value='submit']")))
        print(submit_button)

        phone_number_field.send_keys("09998880000")
        email_field.send_keys("test@example.com")
        password_field.send_keys("Password123Fardin")
        print(password_field)
        print(email_field)
        submit_button.click()
        sleep(3)
        try:
            alert = Alert(self.driver)
            alert_text = alert.text
            assert alert_text == 'Your account is active now please login!'
            alert.accept()
        except:
            pytest.fail(f"Test failed: no alert get from register!")

        link = wait.until(expected_conditions.element_to_be_clickable((By.CSS_SELECTOR, "a[href='/login/']")))
        link.click()

        phone_number_field = wait.until(expected_conditions.presence_of_element_located((By.ID, "phone_number")))
        print(phone_number_field)
        password_field = wait.until(expected_conditions.presence_of_element_located((By.ID, "password")))
        print(password_field)
        submit_button = wait.until(expected_conditions.element_to_be_clickable((By.XPATH, "//button[@value='submit']")))
        print(submit_button)

        phone_number_field.send_keys("09998880000")
        password_field.send_keys("Password123Fardin")

        submit_button.click()
        sleep(5)

        try:
            alert = Alert(self.driver)
            alert_text = alert.text
            assert alert_text == 'Token is valid. User is already logged in.'
            alert.accept()
        except:
            pytest.fail(f"Test failed: no alert get from login!")

        sleep(5)
        jwt_token = self.driver.execute_script("return localStorage.getItem('JWT')")
        print('jwt_token', jwt_token)
        authorization_header_value = f"JWT {jwt_token}"
        # self.driver.execute_cdp_cmd('Network.setExtraHTTPHeaders',
        #                               {'headers': {'Authorization': authorization_header_value}})
        # print(authorization_header_value)
        # sleep(2)
        # self.driver.get('http://localhost:8000/api-v1/auth/users/')
        # sleep(20)
        # pytest.fail(f"Test failed: no alert get from login!")

    def test_product_filtering(self):
        self.driver.get('http://localhost:8000/')
        self.driver.maximize_window()
        # sleep(5)
        # link = driver.find_element_by_link_text("ورود /ثبت نام")
        # link.click()
        wait = WebDriverWait(self.driver, 10)
        link = wait.until(expected_conditions.element_to_be_clickable((By.CSS_SELECTOR, "a[href='/products/']")))
        link.click()

        best_sales = WebDriverWait(self.driver, 10).until(
            expected_conditions.element_to_be_clickable((By.XPATH, "//button[@value='best_sales']")))
        print(best_sales)
        sleep(3)
        best_sales.click()
        sleep(3)
        button = WebDriverWait(self.driver, 10).until(
            expected_conditions.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'ترتیب: best_sales')]")))
        button.click()
        sleep(3)

        button = WebDriverWait(self.driver, 10).until(
            expected_conditions.presence_of_element_located((By.XPATH, "//div[@id='seccondhand']/button[1]")))
        button.click()
        sleep(3)

        button = WebDriverWait(self.driver, 10).until(
            expected_conditions.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'دست دوم: true')]")))
        button.click()
        sleep(3)

        if len(self.driver.find_elements(By.XPATH, "//li[@class='main-nav-list']/a")) > 0:
            category = WebDriverWait(self.driver, 10).until(
                expected_conditions.presence_of_element_located((By.XPATH, "//li[@class='main-nav-list']/a[1]")))
            category.click()
            sleep(3)
            button = WebDriverWait(self.driver, 10).until(
                expected_conditions.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'مجموعه:')]")))
            button.click()
            sleep(3)

        first_li = self.driver.find_element(By.CSS_SELECTOR, 'ul.common-filter > li')

        if first_li:
            first_h6 = first_li.find_element(By.CSS_SELECTOR, 'h6')
            if first_h6:
                first_h6.click()
                sleep(3)

                button = WebDriverWait(self.driver, 10).until(
                    expected_conditions.element_to_be_clickable(
                        (By.XPATH, "//button[contains(text(), 'کلید ویژگی:')]")))
                button.click()
                sleep(3)

        button = WebDriverWait(self.driver, 10).until(
            expected_conditions.element_to_be_clickable((By.ID, "search")))
        button.click()
        sleep(2)

        search_field = wait.until(expected_conditions.presence_of_element_located((By.ID, "search_input")))
        search_field.send_keys('test')
        sleep(1)
        search_field.send_keys(Keys.ENTER)
        sleep(4)
        button = WebDriverWait(self.driver, 10).until(
            expected_conditions.element_to_be_clickable(
                (By.XPATH, "//button[contains(text(), 'جستجو:')]")))
        button.click()
        sleep(3)

    def test_cart_and_adding_items(self):
        self.driver.get('http://localhost:8000/')
        self.driver.maximize_window()
        sleep(5)
        wait = WebDriverWait(self.driver, 10)
        # user_field = wait.until(expected_conditions.presence_of_element_located((By.ID, "username")))
        # print(user_field)
        # passf = wait.until(expected_conditions.presence_of_element_located((By.ID, "password")))
        # print(passf)
        # submit = wait.until(expected_conditions.presence_of_element_located((By.ID, "login_btn_submit")))
        # print(submit)
        # user_field.send_keys('1401010121008')
        # passf.send_keys('0926913638')
        # submit.click()
        # user_field.send_keys('1401010121008')
        link = wait.until(expected_conditions.element_to_be_clickable((By.CSS_SELECTOR, "a[href='/products/']")))
        link.click()
        sleep(5)
        button = wait.until(
            expected_conditions.element_to_be_clickable((By.XPATH, "//p[contains(text(), 'اضافه کردن به سبد')][1]")))
        print(button)
        button.click()
        sleep(5)
        button_2 = wait.until(
            expected_conditions.element_to_be_clickable((By.XPATH, "//button[text()='2']")))
        button_2.click()
        sleep(5)
        button = wait.until(
            expected_conditions.element_to_be_clickable((By.XPATH, "//p[contains(text(), 'توضیحات')][1]")))
        button.click()
        sleep(5)
        element = wait.until(expected_conditions.element_to_be_clickable((By.CSS_SELECTOR, "i.lnr.lnr-chevron-up")))
        element.click()
        sleep(1)
        element.click()
        sleep(1)
        element.click()
        sleep(2)
        input_element = wait.until(
            expected_conditions.element_to_be_clickable((By.ID, "sst")))
        input_value = input_element.get_attribute("value")
        assert input_value == "4", "The input value is not equal to 4"
        button = wait.until(
            expected_conditions.element_to_be_clickable((By.ID, "addToCartBtn")))
        button.click()
        sleep(5)
        try:
            alert = Alert(self.driver)
            alert_text = alert.text
            assert alert_text == 'Item added to cart successfully!'
            alert.accept()
        except:
            pytest.fail(f"Test failed: no alert get from login!")

        sleep(5)
        link = wait.until(expected_conditions.element_to_be_clickable((By.CSS_SELECTOR, "a[href='/cart/']")))
        link.click()
        sleep(5)
        delete_button = wait.until(expected_conditions.element_to_be_clickable((By.XPATH,
                                                                                "//button[contains(@class, 'genric-btn') and contains(@class, 'danger')][1]")))
        delete_button.click()
        sleep(5)
        increase_button = wait.until(expected_conditions.element_to_be_clickable((By.XPATH,
                                                                                  "//button[contains(@class, 'increase') and contains(@class, 'items-count')]")))
        increase_button.click()
        sleep(7)
        quantity_input = wait.until(
            expected_conditions.visibility_of_element_located((By.XPATH, "//input[contains(@id, 'quantity-')]")))
        quantity_value = quantity_input.get_attribute("value")
        assert quantity_value == "5", "The input value is not equal to 5"
        sleep(15)
