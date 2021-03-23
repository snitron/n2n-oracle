pragma solidity ^0.6.0;

contract ValidatorsManagement{
    uint256 threshold;
    address[] validators;
    address owner;
    
    constructor (address[] memory _validators, uint256 _threshold) public {
        require (_threshold <= _validators.length);
        validators = _validators;
        threshold = _threshold;
        owner = msg.sender;
    }
    
    
    function addValidator(address newvalidator) external {
        require(msg.sender == owner);
        bool is_validator_norm = true;
        for (uint256 i = 0; i < validators.length; i++){
            if (validators[i] == newvalidator){
                is_validator_norm = false;
            }
        }
        require(is_validator_norm);
        validators.push(newvalidator);
    }
    
    function removeValidator(address validator) external {
        require(msg.sender == owner);
        require(validators.length > threshold);
        bool is_validator_exist = false;
        for (uint256 i = 0; i < validators.length; i++){
            if (validators[i] == validator){
                is_validator_exist = true;

                validators[i] = validators[validators.length - 1];
                validators.pop();
                break;
            }
        }

        require(is_validator_exist);
    }
    
    function changeThreshold(uint256 thresh) external {
        require(msg.sender == owner);
        require(validators.length >= thresh);
        threshold = thresh;
    }
    
    function getThreshold() view public returns (uint256){
        return threshold;
    }
    
    function getValidators() view public returns (address[] memory){
        return validators;
    }
   
} 
