// Admin login form validation and submission
const adminLoginForm = document.querySelector('#adminLoginForm');
if (adminLoginForm) {
  adminLoginForm.addEventListener('submit', async function(event) {
    event.preventDefault(); // Prevent the default form submission

    const username = document.getElementById('adminUsername').value;
    const password = document.getElementById('adminPassword').value;

    // Basic validation
    if (!username || !password) {
      alert('Please fill in all fields.');
      return;
    }

    try {
      const formData = new FormData();
      formData.append('username', username);
      formData.append('password', password);

      const response = await fetch('/loginadmin', {
        method: 'POST',
        body: formData
      });

      const result = await response.text();
      alert(result); // Display the result message

      if (response.ok) {
        window.location.href = '/admin'; // Redirect on successful login
      } else {
        // Show error message for incorrect login
        alert('Admin username or password is incorrect.');
      }
    } catch (error) {
      console.error('Error:', error);
      alert('An error occurred. Please try again later.');
    }
  });
}

// Login form validation and submission
const loginForm = document.querySelector('#loginForm');
if (loginForm) {
  loginForm.addEventListener('submit', async function(event) {
    event.preventDefault(); // Prevent the default form submission

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;

    // Basic validation
    if (!username || !password) {
      alert('Please fill in all fields.');
      return;
    }

    try {
      const formData = new FormData();
      formData.append('username', username);
      formData.append('password', password);

      const response = await fetch('/login', {
        method: 'POST',
        body: formData
      });

      const result = await response.text();
      alert(result); // Display the result message

      if (response.ok) {
        window.location.href = '/chatbot'; // Redirect on successful login
      } else {
        alert('Incorrect username or password.'); // Display error message for incorrect login
      }
    } catch (error) {
      console.error('Error:', error);
      alert('An error occurred. Please try again later.');
    }
  });
}

// Register form validation and submission
const registerForm = document.querySelector('#registerForm');
if (registerForm) {
  registerForm.addEventListener('submit', function(event) {
    event.preventDefault(); // Prevent the default form submission
    validateRegisterForm(); // Call the validation function
  });
}

function validateRegisterForm() {
  const name = document.getElementById('name').value;
  const username = document.getElementById('username').value;
  const email = document.getElementById('email').value;
  const phone = document.getElementById('phone').value;
  const password = document.getElementById('password').value;

  let errorMessages = [];

  if (!name || !username || !email || !phone || !password) {
    errorMessages.push("Please fill in all fields.");
  }
  const phonePattern = /^\d{10,14}$/;
  if (!phonePattern.test(phone)) {
    errorMessages.push("Please enter a valid phone number with 10-14 digits.");
  }

  const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailPattern.test(email)) {
    errorMessages.push("Please enter a valid email address.");
  }

  const passwordPattern = /^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$/;
  if (!passwordPattern.test(password)) {
    errorMessages.push("Password must contain at least 8 characters, including both letters and numbers.");
  }

  if (errorMessages.length > 0) {
    alert(errorMessages.join("\n"));
  } else {
    submitRegistrationForm();
  }
}

async function submitRegistrationForm() {
  const formData = new FormData(registerForm);
  
  try {
    const response = await fetch('/register', {
      method: 'POST',
      body: formData
    });

    const result = await response.text();
    alert(result); // Display the result message

    if (response.ok) {
      registerForm.reset();
    }
  } catch (error) {
    console.error('Error:', error);
    alert('Registration failed. Please try again later.');
  }
}

// Contact form validation and submission
const contactForm = document.querySelector('#contactForm');
if (contactForm) {
  contactForm.addEventListener('submit', async function(event) {
    event.preventDefault(); 

    const nameInput = document.getElementById('name');
    const emailInput = document.getElementById('email');
    const phoneInput = document.getElementById('phone');
    const messageInput = document.getElementById('message');

    if (!nameInput.value.trim() || !emailInput.value.trim() || !phoneInput.value.trim() || !messageInput.value.trim()) {
      alert('Please fill in all fields.'); 
      return; 
    }

    try {
      const response = await fetch('/contact', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          name: nameInput.value,
          email: emailInput.value,
          phone: phoneInput.value,
          message: messageInput.value
        })
      });

      const result = await response.text();
      alert(result); // Display the result message

      // Reset the form on successful submission
      if (response.ok) {
        contactForm.reset();
      }

    } catch (error) {
      console.error('Error:', error);
      alert('Error sending message, please try again.');
    }
  });
}

// Chatbot interaction
const textSubmit = document.getElementById('textSubmit');
const voiceSubmit = document.getElementById('voiceSubmit');
const userInput = document.getElementById('userInput');
const botContent = document.querySelector('.botcontent');

textSubmit.addEventListener('click', function() {
  const message = userInput.value;
  if (message.trim() === '') return;

  appendMessage('user', message);
  userInput.value = '';

  // Call the chatbot function to get a response
  getChatbotResponse(message);
});

voiceSubmit.addEventListener('click', function() {
  voiceSubmit.classList.add('hover-effect');
  fetch('/speech_to_text', {
    method: 'POST'
  })
  .then(response => response.text())
  .then(data => {
    const message = data;
    appendMessage('user', message);
    getChatbotResponse(message);
  })
  .catch(error => console.error('Error:', error))
  .finally(() => {
    voiceSubmit.classList.remove('hover-effect');
  });
});

function appendMessage(sender, message) {
  const messageElement = document.createElement('div');
  messageElement.classList.add('message', sender);
  messageElement.textContent = message;
  botContent.appendChild(messageElement);
}

function getChatbotResponse(message) {
  fetch('/chatbot', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
    body: new URLSearchParams({ message: message }),
  })
  .then(response => response.text())
  .then(data => {
    appendMessage('bot', data);
  })
  .catch(error => console.error('Error:', error));
}
