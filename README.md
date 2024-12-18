# Parking Management System

A web-based parking management system that includes features such as barrier control, violation reporting, and license plate recognition. This project is designed for controlling a simple parking prototype and is built with Flask, OpenCV, and real-time logging.

## Installation

Follow these steps to set up and run the application:

1. Clone the Repository

```sh
git clone https://github.com/ekl3m/cyber-parking.git
```

2. Navigate to the Project Directory

```sh
cd cyber-parking
```

3. Install Dependencies

```sh
pip install -r requirements.txt
```

4. Run the Application

```sh
python app.py
```

## Usage

Access the app via a browser at `http://localhost:8080/` to control the parking system. You can:

- Switch between live camera feed and video playback.
- Monitor parking violations and control barriers.

## Technologies Used

- **Flask**: Web framework for building the app.
- **OpenCV**: For live video processing and license plate recognition.
- **Real-time logging**: To track events and status changes in the system.

## Contribution

To contribute to this project, follow these steps:

### Commit Pattern:

Use the format `"VX.X.X : Description of the change"` where `X` is a natural number.

### Example:

```sh
git commit -m "V0.1.0 : Added parking violation reporting feature"
```

### Steps to Contribute:

1. Fork the repository.
2. Create a new branch for your feature or fix:

```sh
git checkout -b feature/your-feature
```

3. Make your changes and test them.
4. Commit your changes:

```sh
git commit -m "VX.X.X - Description of the change"
```

5. Push to your branch:

```sh
git push origin feature/your-feature
```

6. Open a pull request.

## License

This project is licensed under the Creative Commons BY-NC-ND license to ekl3m. See the `"LICENSE"` tab for more details.

## Contact

For questions or support, feel free to reach out:

- Email: sq.programs@gmail.com
- GitHub: ekl3m
