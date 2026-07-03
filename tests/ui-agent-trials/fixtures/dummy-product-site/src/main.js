import products from './products.js';

const productList = document.getElementById('product-list');

if (productList) {
  if (products.length === 0) {
    productList.textContent = 'No products available yet.';
  } else {
    products.forEach((product) => {
      const productElement = document.createElement('div');
      productElement.classList.add('product-card');
      productElement.innerHTML = `
        <h2>${product.name}</h2>
        <p>Category: ${product.category}</p>
        <p>Description: ${product.description}</p>
        <p>$${product.price}</p>
      `;
      productList.appendChild(productElement);
    });
  }
}
