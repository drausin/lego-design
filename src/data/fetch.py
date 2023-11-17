# This is a new file. Add your Python code here.
import argparse
import os
import time
import zipfile

from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def ldraw_parts(data_dir: str):
    url = "http://www.ldraw.org/library/updates/complete.zip"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    response = requests.get(url)
    zip_path = os.path.join(data_dir, "complete.zip")

    with open(zip_path, "wb") as f:
        f.write(response.content)

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(data_dir)
    print(f"Extracted {len(zip_ref.namelist())} files")


def ldraw_part_images(data_dir: str):
    url = 'https://rebrickable.com/downloads/'
    response = requests.get(url)
    response.raise_for_status()  # Ensure the request was successful

    images_dir = os.path.join(data_dir, 'ldraw_images')
    os.makedirs(images_dir, exist_ok=True)

    soup = BeautifulSoup(response.text, 'html.parser')
    links = soup.find_all('a', href=True)

    for link in links:
        href = link['href']
        if href.endswith('.zip'):
            try:
                download_response = requests.get(href)
                download_response.raise_for_status()

                filename = href.split('/')[-1]
                file_path = os.path.join(images_dir, filename)

                with open(file_path, 'wb') as file:
                    file.write(download_response.content)
                print(f'Downloaded {filename} to {file_path}')

                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(images_dir)
                print(f"Extracted {len(zip_ref.namelist())} files")

            except Exception as e:
                print(f'Failed to download {href}: {e}')


def ldraw_models(data_dir: str):
    base_url = "https://omr.ldraw.org/files"
    driver = webdriver.Chrome()  # or use any other webdriver
    driver.get(base_url)

    try:
        # Wait for the dynamic content to load
        WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, ".table"))
        )

        while True:
            # Process the current page
            set_links = driver.find_elements(By.TAG_NAME, 'a')
            print(f"found {len(set_links)} links")
            for link in set_links:
                href = link.get_attribute('href')
                if href and '/files/' in href:
                    model_number = href.split('/')[-1]
                    filename = model_number + '.mpd'
                    filepath = os.path.join(data_dir, 'models', filename)
                    if os.path.exists(filepath):
                        print(f"Skipping downloading model number {model_number} because it already exists locally")
                        continue

                    # Open each set link in a new tab
                    driver.execute_script(f"window.open('{href}', 'new_window')")
                    driver.switch_to.window(driver.window_handles[1])

                    # Wait for the page to load
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "btn-success"))
                    )

                    # Find the download link
                    download_link = driver.find_element(By.CLASS_NAME, 'btn-success').get_attribute('href')

                    if download_link:
                        download_response = requests.get(download_link)
                        download_response.raise_for_status()
                        os.makedirs(os.path.join(data_dir, 'models'), exist_ok=True)
                        with open(filepath, 'wb') as file:
                            file.write(download_response.content)
                        print(f'Downloaded model to {filename}')

                    # Close the current tab and switch back to the main page
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                    time.sleep(1)  # Small delay to avoid rapid opening and closing of tabs

            # Find the 'Next' button
            try:
                next_button = driver.find_element(By.XPATH, "//a[@data-page][contains(text(), 'Next')]")
                if "disabled" in next_button.find_element(By.XPATH, "..").get_attribute("class"):
                    break  # Stop if 'Next' button is disabled
                print("Moving to Next page")
                next_button.click()
                time.sleep(5)  # Delay to allow next set of results loading
                WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, ".table"))
                )
            except NoSuchElementException as e:
                print("Next button not visible. Stopping")
                break

    finally:
        driver.quit()


def catalog_db(data_dir: str):
    url = 'https://rebrickable.com/downloads/'
    response = requests.get(url)
    response.raise_for_status()  # Ensure the request was successful

    catalog_dir = os.path.join(data_dir, 'catalog_db')
    os.makedirs(catalog_dir, exist_ok=True)

    soup = BeautifulSoup(response.text, 'html.parser')
    links = soup.find_all('a', href=True)

    for link in links:
        href = link['href']
        if 'csv.gz' in href:
            try:
                download_response = requests.get(href)
                download_response.raise_for_status()

                filename = href.split('/')[-1].split('?')[0]  # Remove URL parameters
                file_path = os.path.join(catalog_dir, filename)

                with open(file_path, 'wb') as file:
                    file.write(download_response.content)
                print(f'Downloaded {filename} to {file_path}')
            except Exception as e:
                print(f'Failed to download {href}: {e}')


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=["ldraw-parts", "ldraw-part-images", "ldraw-models", "catalog-db"],
        help="The command to run",
    )
    parser.add_argument("--data-dir", default="./data", help="The local data directory")
    args = parser.parse_args()

    if args.command == "ldraw-parts":
        ldraw_parts(args.data_dir)
    elif args.command == "ldraw-part-images":
        ldraw_part_images(args.data_dir)
    elif args.command == "ldraw-models":
        ldraw_models(args.data_dir)
    elif args.command == "catalog-db":
        catalog_db(args.data_dir)
    else:
        print(f"unexpected command: {args.command}")
